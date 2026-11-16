"""
Unit tests for Uploaded Document NLP Pipeline.
Raksha AI Stage 3 Solid — Floor 2 (Language & Knowledge Agents)
Owner: Ary
"""
from datetime import datetime, timezone
import io
import unittest

from agents.extraction.agent import ExtractionAgent
from agents.resolution.agent import ResolutionAgent
from agents.resolution.feedback import (
    FeedbackDecision,
    FeedbackRecord,
    ResolutionFeedbackStore,
)
from agents.threading.agent import ThreadingAgent
from agents.translation.agent import TranslationAgent
from common.schemas.provenance import ClaimStatus, SourceType
from pipeline.upload_nlp import (
    DocumentChunk,
    DocumentTooLargeError,
    EmptyDocumentError,
    UploadedDocumentAnalysis,
    UploadedDocumentNLPPipeline,
    UnsupportedFormatError,
    clean_document_text,
    chunk_document_text,
    extract_text_from_upload,
)


class TestUploadNLPPipeline(unittest.TestCase):
    def setUp(self):
        self.t0 = datetime(2026, 11, 16, 10, 0, 0, tzinfo=timezone.utc)
        self.pipeline = UploadedDocumentNLPPipeline(
            chunk_size=400,
            chunk_overlap=80,
        )

    # ── 1. Noisy Text Cleanup Tests ──

    def test_noisy_text_cleanup_normalizes_whitespace_and_null_bytes(self):
        """Null bytes and weird unicode spaces are sanitized, preserving coordinates and ranks."""
        dirty = (
            "CONFIDENTIAL\n"
            "Lt. Gen. Upendra Dwivedi visited forward post.\x00\x08\n"
            "Coordinates:\u00a0 34.12,\t 77.58.\r\n"
            "Date: 2026-11-16. Rafale jets conducted CAP.\n"
            "PAGE 1 OF 5\n"
        )
        cleaned = clean_document_text(dirty)
        self.assertNotIn("\x00", cleaned)
        self.assertNotIn("\u00a0", cleaned)
        self.assertNotIn("\r", cleaned)
        self.assertNotIn("CONFIDENTIAL", cleaned)
        self.assertNotIn("PAGE 1 OF 5", cleaned)
        # Critical intelligence tokens must be preserved
        self.assertIn("Lt. Gen. Upendra Dwivedi", cleaned)
        self.assertIn("34.12", cleaned)
        self.assertIn("77.58", cleaned)
        self.assertIn("2026-11-16", cleaned)
        self.assertIn("Rafale", cleaned)

    def test_noisy_text_cleanup_empty_or_none(self):
        self.assertEqual(clean_document_text(""), "")
        self.assertEqual(clean_document_text(None), "")

    # ── 2. Long Document Chunking & Boundaries ──

    def test_chunking_sentence_boundaries_and_overlap(self):
        """Chunking respects sentence boundaries and maintains configured overlap."""
        text = (
            "Sentence one discusses Indian Army movements in Eastern Ladakh. "
            "Sentence two discusses Indian Air Force combat air patrols over Pangong Tso. "
            "Sentence three highlights DRDO surveillance drones monitoring the Line of Actual Control. "
            "Sentence four notes naval preparedness by the Indian Navy in the Arabian Sea."
        )
        chunks = chunk_document_text(text, chunk_size=160, chunk_overlap=40, document_id="doc_test")
        self.assertGreaterEqual(len(chunks), 2)

        for i, c in enumerate(chunks):
            self.assertEqual(c.document_id, "doc_test")
            self.assertIn(f"doc_test_c{i}", c.chunk_id)
            self.assertLessEqual(len(c.text), 180)  # within sentence boundary margin
            self.assertGreater(len(c.text), 0)

        # Test overlap continuity: some tokens from chunk 0 must exist in chunk 1
        words_c0 = set(chunks[0].text.split())
        words_c1 = set(chunks[1].text.split())
        common_words = words_c0 & words_c1
        self.assertGreater(len(common_words), 0)

    def test_chunking_with_page_map(self):
        """Page map chunking assigns exact page numbers to chunk provenance."""
        page_map = {
            1: "Page one report on IAF deployment.",
            2: "Page two intelligence on PLA troop mobilization across LAC.",
        }
        chunks = chunk_document_text(
            text="",  # Ignored when page_map provided
            chunk_size=200,
            chunk_overlap=30,
            page_map=page_map,
            document_id="pdf_doc",
        )
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].page_number, 1)
        self.assertIn("p1", chunks[0].chunk_id)
        self.assertIn("IAF", chunks[0].text)

        self.assertEqual(chunks[1].page_number, 2)
        self.assertIn("p2", chunks[1].chunk_id)
        self.assertIn("PLA", chunks[1].text)

    def test_chunking_invalid_parameters_raise_value_error(self):
        with self.assertRaises(ValueError):
            chunk_document_text("valid text", chunk_size=0)
        with self.assertRaises(ValueError):
            chunk_document_text("valid text", chunk_size=100, chunk_overlap=-1)
        with self.assertRaises(ValueError):
            chunk_document_text("valid text", chunk_size=100, chunk_overlap=100)
        with self.assertRaises(ValueError):
            chunk_document_text("valid text", chunk_size=100, chunk_overlap=120)

    # ── 3. Empty and Malformed Documents ──

    def test_empty_documents_raise_error(self):
        """0-byte and whitespace-only uploads raise EmptyDocumentError."""
        with self.assertRaises(EmptyDocumentError):
            extract_text_from_upload(b"", filename="empty.txt")
        with self.assertRaises(EmptyDocumentError):
            extract_text_from_upload(b"   \n\t   ", filename="blank.txt")
        with self.assertRaises(EmptyDocumentError):
            extract_text_from_upload(b",,\n,,", filename="blank.csv")

    # ── 4. Unsupported Formats & Security Boundaries ──

    def test_unsupported_extensions_and_executable_magic_bytes_rejected(self):
        """Executables, zips, and unsupported extensions are rejected."""
        # Unsupported extension
        with self.assertRaises(UnsupportedFormatError):
            extract_text_from_upload(b"some content", filename="doc.docx")

        # PE Executable (MZ header)
        with self.assertRaises(UnsupportedFormatError):
            extract_text_from_upload(b"MZ\x90\x00malicious", filename="test.txt")

        # ELF Executable
        with self.assertRaises(UnsupportedFormatError):
            extract_text_from_upload(b"\x7fELF\x02malicious", filename="test.txt")

        # Zip Archive (PK header)
        with self.assertRaises(UnsupportedFormatError):
            extract_text_from_upload(b"PK\x03\x04archive", filename="test.txt")

    def test_file_exceeding_max_size_raises_document_too_large(self):
        """Documents over 15MB are rejected."""
        oversized = b"A" * (16 * 1024 * 1024)
        with self.assertRaises(DocumentTooLargeError):
            extract_text_from_upload(oversized, filename="oversized.txt")

    # ── 5. End-to-End Pipeline & Provenance Preservation ──

    def test_end_to_end_pipeline_txt_document(self):
        """Uploaded text document executes full pipeline with mandatory user_upload provenance."""
        txt_content = (
            "DEFENCE INTELLIGENCE BULLETIN\n"
            "Indian Air Force scrambled Su-30MKI fighters following radar detection near LAC.\n"
            "Defence Research and Development Organisation tested a long-range glide bomb.\n"
            "Indian Army units in Leh confirmed full operational readiness.\n"
        )
        analysis = self.pipeline.process_document(
            content=txt_content.encode("utf-8"),
            filename="intel_bulletin.txt",
            workspace_id=101,
            document_id="doc_bulletin_101",
        )

        self.assertIsInstance(analysis, UploadedDocumentAnalysis)
        self.assertEqual(analysis.document_id, "doc_bulletin_101")
        self.assertEqual(analysis.workspace_id, "101")
        self.assertEqual(analysis.source_type, "user_upload")
        self.assertEqual(analysis.format, "txt")
        self.assertGreater(len(analysis.chunks), 0)

        # Verify provenance
        self.assertIsNotNone(analysis.provenance)
        self.assertEqual(analysis.provenance.source_type, SourceType.USER_UPLOAD)
        self.assertEqual(analysis.provenance.claim_status, ClaimStatus.REPORTED)

        # Check resolved entities contain user_upload source_type and trusted workspace_id
        self.assertGreater(len(analysis.resolved_entities), 0)
        canonical_names = {e["canonical_name"] for e in analysis.resolved_entities}
        self.assertIn("Indian Air Force", canonical_names)
        self.assertIn("Defence Research and Development Organisation", canonical_names)

        for ent in analysis.resolved_entities:
            self.assertEqual(ent["source_type"], "user_upload")
            self.assertEqual(ent["workspace_id"], "101")
            self.assertEqual(ent["document_id"], "doc_bulletin_101")
            self.assertIn("chunk_id", ent)

        # Check threading output
        self.assertGreater(len(analysis.event_threads), 0)
        thread = analysis.event_threads[0]
        self.assertEqual(thread["source_type"], "user_upload")
        self.assertEqual(thread["workspace_id"], "101")

    def test_end_to_end_pipeline_csv_document(self):
        """CSV documents are parsed row-by-row and processed through NLP pipeline."""
        csv_content = (
            "date,headline,unit,region\n"
            "2026-11-16,IAF conducts aerial drills,Indian Air Force,Ladakh\n"
            "2026-11-15,DRDO flight test conducted,DRDO,Odisha\n"
        )
        analysis = self.pipeline.process_document(
            content=csv_content.encode("utf-8"),
            filename="drills.csv",
            workspace_id=202,
        )
        self.assertEqual(analysis.format, "csv")
        self.assertEqual(analysis.workspace_id, "202")
        self.assertEqual(analysis.source_type, "user_upload")

        canonical_names = {e["canonical_name"] for e in analysis.resolved_entities}
        self.assertIn("Indian Air Force", canonical_names)
        self.assertIn("Defence Research and Development Organisation", canonical_names)

    # ── 6. Strict Workspace Isolation & Anti-Leakage ──

    def test_workspace_isolation_custom_feedback_not_accessible_across_workspaces(self):
        """
        Feedback ingested in workspace 101 must resolve for workspace 101 uploads,
        but must NOT affect workspace 102 uploads of the same document text.
        """
        custom_alias = "Project Garuda Stealth Platform"
        # Ingest accepted feedback in workspace 101: Project Garuda -> Indian Air Force
        rec_101 = FeedbackRecord(
            source_mention=custom_alias,
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-garuda-101",
            reviewed_at=self.t0,
            workspace_id=101,
        )
        self.pipeline.resolution_agent.add_feedback_records(rec_101)

        doc_text = f"Classified update: {custom_alias} was deployed to forward air base."

        # Process in workspace 101 -> resolves to IAF via feedback
        res_101 = self.pipeline.process_document(
            content=doc_text,
            filename="garuda_report.txt",
            workspace_id=101,
        )
        resolved_101 = {e["raw_name"]: e for e in res_101.resolved_entities}
        self.assertIn(custom_alias, resolved_101)
        self.assertEqual(resolved_101[custom_alias]["action"], "auto_link")
        self.assertEqual(resolved_101[custom_alias]["canonical_name"], "Indian Air Force")
        self.assertEqual(resolved_101[custom_alias]["claim_status"], ClaimStatus.ANALYST_VERIFIED.value)

        # Process exact same document in workspace 102 -> zero leakage of workspace 101 feedback!
        res_102 = self.pipeline.process_document(
            content=doc_text,
            filename="garuda_report.txt",
            workspace_id=102,
        )
        resolved_102 = {e["raw_name"]: e for e in res_102.resolved_entities}
        # Workspace 102 has no access to workspace 101's feedback record
        self.assertNotIn(custom_alias, resolved_102)

        # Verify negative constraint isolation as well:
        # In workspace 101, reject IAF -> Indian Air Force
        rec_neg_101 = FeedbackRecord(
            source_mention="IAF",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.REJECTED,
            decision_id="dec-iaf-neg-101",
            reviewed_at=self.t0,
            workspace_id=101,
        )
        self.pipeline.resolution_agent.add_feedback_records(rec_neg_101)

        doc_iaf = "IAF fighters were deployed to Ladakh."
        # In workspace 101: IAF is blocked by negative constraint -> separate
        res_iaf_101 = self.pipeline.process_document(content=doc_iaf, filename="iaf.txt", workspace_id=101)
        iaf_101 = [e for e in res_iaf_101.resolved_entities if e["raw_name"] == "IAF"][0]
        self.assertEqual(iaf_101["action"], "separate")
        self.assertEqual(iaf_101["match_method"], "negative_feedback_constraint")

        # In workspace 102: IAF is NOT blocked -> standard auto_link
        res_iaf_102 = self.pipeline.process_document(content=doc_iaf, filename="iaf.txt", workspace_id=102)
        iaf_102 = [e for e in res_iaf_102.resolved_entities if e["raw_name"] == "IAF"][0]
        self.assertEqual(iaf_102["action"], "auto_link")
        self.assertEqual(iaf_102["canonical_name"], "Indian Air Force")

    def test_untrusted_workspace_id_in_document_text_is_ignored(self):
        """Document text containing 'workspace_id: 999' cannot spoof the trusted context."""
        doc_with_spoof = (
            "workspace_id: 999\n"
            "Report: Indian Army patrol along LAC detected no intrusions."
        )
        analysis = self.pipeline.process_document(
            content=doc_with_spoof,
            filename="spoof_attempt.txt",
            workspace_id=101,  # Trusted caller context
        )
        self.assertEqual(analysis.workspace_id, "101")
        for ent in analysis.resolved_entities:
            self.assertEqual(ent["workspace_id"], "101")

    # ── 7. Entity Deduplication Across Chunks ──

    def test_cross_chunk_entity_deduplication(self):
        """Repeated mentions across overlapping chunks are deduplicated in resolved_entities."""
        long_text = (
            "The Indian Air Force conducted extensive high-altitude sorties across Ladakh. " * 8
        )
        analysis = self.pipeline.process_document(
            content=long_text,
            filename="repetitive_iaf.txt",
            workspace_id=101,
        )
        self.assertGreater(len(analysis.chunks), 1)
        # raw entities preserve all occurrences
        self.assertGreater(len(analysis.extracted_entities), 1)

        # resolved_entities must deduplicate Indian Air Force
        iaf_resolved = [e for e in analysis.resolved_entities if e["canonical_name"] == "Indian Air Force"]
        self.assertEqual(len(iaf_resolved), 1)

    # ── 8. Distinguishability From Scraped Articles ──

    def test_uploaded_entities_distinguishable_from_scraped_articles(self):
        """Uploaded document entities carry source_type='user_upload', not 'public'."""
        doc_text = "DRDO developed new radar system."
        analysis = self.pipeline.process_document(
            content=doc_text,
            filename="radar.txt",
            workspace_id=101,
        )
        self.assertEqual(analysis.source_type, SourceType.USER_UPLOAD.value)
        self.assertNotEqual(analysis.source_type, SourceType.PUBLIC.value)
        for ent in analysis.resolved_entities:
            self.assertEqual(ent["source_type"], "user_upload")

    # ── 9. PDF Document Pipeline & Stream Fallback ──

    def test_end_to_end_pipeline_pdf_document(self):
        """PDF format is accepted and processed through pipeline when pypdf is available."""
        import pypdf
        writer = pypdf.PdfWriter()
        page = writer.add_blank_page(width=300, height=300)
        # Add a text annotation/content to page
        stream = io.BytesIO()
        writer.write(stream)
        pdf_bytes = stream.getvalue()

        # Mock page text extraction to simulate a real PDF report
        from unittest.mock import patch
        with patch("pypdf.PdfReader") as mock_reader_cls:
            mock_reader = mock_reader_cls.return_value
            mock_page = unittest.mock.MagicMock()
            mock_page.extract_text.return_value = (
                "Indian Army conducted defensive exercises in Ladakh near Line of Actual Control."
            )
            mock_reader.pages = [mock_page]

            analysis = self.pipeline.process_document(
                content=pdf_bytes,
                filename="exercise_report.pdf",
                workspace_id=101,
            )
            self.assertEqual(analysis.format, "pdf")
            self.assertEqual(analysis.workspace_id, "101")
            self.assertEqual(analysis.source_type, "user_upload")
            self.assertGreater(len(analysis.chunks), 0)
            canonical_names = {e["canonical_name"] for e in analysis.resolved_entities}
            self.assertIn("Indian Army", canonical_names)

    def test_pdf_dependency_missing_raises_clear_error(self):
        """When pypdf is unavailable, a clear DependencyMissingError is raised instructing coordination with Jay."""
        from unittest.mock import patch
        from pipeline.upload_nlp import DependencyMissingError
        with patch.dict("sys.modules", {"pypdf": None}):
            with self.assertRaises(DependencyMissingError) as ctx:
                extract_text_from_upload(b"%PDF-1.4...", filename="report.pdf")
            self.assertIn("pypdf", str(ctx.exception))
            self.assertIn("Jay", str(ctx.exception))

    # ── 10. Repeated Ingestion & Idempotency ──

    def test_repeated_document_processing_is_idempotent(self):
        """Processing the exact same document bytes produces deterministic, identical outputs."""
        content = "Indian Navy deployed stealth frigates across the Arabian Sea during tactical drills."
        res1 = self.pipeline.process_document(content=content, filename="navy.txt", workspace_id=101)
        res2 = self.pipeline.process_document(content=content, filename="navy.txt", workspace_id=101)

        self.assertEqual(res1.document_id, res2.document_id)
        self.assertEqual(len(res1.chunks), len(res2.chunks))
        self.assertEqual(len(res1.resolved_entities), len(res2.resolved_entities))
        self.assertEqual(
            [e["canonical_name"] for e in res1.resolved_entities],
            [e["canonical_name"] for e in res2.resolved_entities],
        )

    # ── 11. Automatic Language Detection Tests (Fix 1) ──

    def test_language_detection_hindi_text(self):
        """Real Hindi text is detected as 'hi' and translated via translation engine."""
        hi_text = "भारतीय वायु सेना ने लद्दाख में नए सुखोई लड़ाकू विमान तैनात किए और युद्धाभ्यास किया।"
        analysis = self.pipeline.process_document(
            content=hi_text,
            filename="hindi_report.txt",
            workspace_id=101,
        )
        self.assertEqual(analysis.detected_language, "hi")
        self.assertGreater(len(analysis.chunks), 0)

    def test_language_detection_urdu_text(self):
        """Real Urdu text is detected as 'ur' and routed to translation."""
        ur_text = "پاک فضائیہ نے سرحد کے قریب گشت شروع کر دی اور دفاعی تیاریوں کا جائزہ لیا۔"
        analysis = self.pipeline.process_document(
            content=ur_text,
            filename="urdu_report.txt",
            workspace_id=101,
        )
        self.assertEqual(analysis.detected_language, "ur")

    def test_language_detection_punjabi_text(self):
        """Real Punjabi text is detected as 'pa', preserved, and flagged as unsupported by translator."""
        pa_text = "ਭਾਰਤੀ ਫੌਜ ਨੇ ਸਰਹੱਦ ਤੇ ਜਵਾਨ ਤਾਇਨਾਤ ਕੀਤੇ ਹਨ ਅਤੇ ਸੁਰੱਖਿਆ ਚੌਕਸੀ ਵਧਾ ਦਿੱਤੀ ਹੈ।"
        analysis = self.pipeline.process_document(
            content=pa_text,
            filename="punjabi_report.txt",
            workspace_id=101,
        )
        self.assertEqual(analysis.detected_language, "pa")
        # Text is preserved without crashing or incorrectly claiming translation
        self.assertIn("ਭਾਰਤੀ ਫੌਜ", analysis.chunks[0].text)
        self.assertTrue(any("pa" in w and "not supported" in w for w in analysis.warnings))

    def test_language_detection_bengali_text(self):
        """Real Bengali text is detected as 'bn', preserved, and flagged as unsupported by translator."""
        bn_text = "ভারতীয় সেনা সীমান্তে নজরদারি বৃদ্ধি করেছে এবং সতর্কতামূলক ব্যবস্থা গ্রহণ করেছে।"
        analysis = self.pipeline.process_document(
            content=bn_text,
            filename="bengali_report.txt",
            workspace_id=101,
        )
        self.assertEqual(analysis.detected_language, "bn")
        self.assertIn("ভারতীয় সেনা", analysis.chunks[0].text)
        self.assertTrue(any("bn" in w and "not supported" in w for w in analysis.warnings))

    def test_language_detection_english_text(self):
        """Real English text is detected as 'en' with passthrough."""
        en_text = "Indian Air Force scrambled fighters along the Line of Actual Control."
        analysis = self.pipeline.process_document(
            content=en_text,
            filename="english_report.txt",
            workspace_id=101,
        )
        self.assertEqual(analysis.detected_language, "en")

    def test_language_detection_mixed_language_text(self):
        """Mixed English-Hindi document identifies script and translates non-English segments."""
        mixed_text = (
            "IAF patrol reported military activity: "
            "भारतीय वायु सेना ने लद्दाख में युद्धाभ्यास किया।"
        )
        analysis = self.pipeline.process_document(
            content=mixed_text,
            filename="mixed_report.txt",
            workspace_id=101,
        )
        self.assertIn(analysis.detected_language, ("hi", "en"))
        self.assertGreater(len(analysis.chunks), 0)

    def test_language_detection_very_short_text(self):
        """Short Latin and short Indic snippets use script heuristics rather than random assignment."""
        from pipeline.upload_nlp import detect_document_language
        lang_latin, conf_latin, _ = detect_document_language("Indian Army")
        self.assertEqual(lang_latin, "en")

        lang_indic, conf_indic, _ = detect_document_language("सेना")
        self.assertEqual(lang_indic, "hi")

        lang_sym, conf_sym, _ = detect_document_language("--- 12345 ---")
        self.assertEqual(lang_sym, "unknown")

    def test_language_detection_empty_text(self):
        """Empty text raises EmptyDocumentError."""
        with self.assertRaises(EmptyDocumentError):
            self.pipeline.process_document(content="", filename="empty.txt", workspace_id=101)

    def test_language_detection_unsupported_language_input(self):
        """Unsupported languages (e.g. French) are detected, preserved, and warning emitted."""
        fr_text = "Les forces armees ont deployee des troupes pres de la frontiere pour des exercices militaires."
        analysis = self.pipeline.process_document(
            content=fr_text,
            filename="french.txt",
            workspace_id=101,
        )
        self.assertEqual(analysis.detected_language, "fr")
        self.assertTrue(any("fr" in w and "not supported" in w for w in analysis.warnings))

    # ── 12. Conservative Event-Evidence Gate Tests (Fix 2) ──

    def test_event_gate_generic_document_with_no_entities_skips_threading(self):
        """Generic administrative document with no entities skips event thread seeding."""
        generic_text = (
            "Standard operating procedure for annual office supply requisition and warehouse inventories. "
            "All department heads must submit paperwork before Friday."
        )
        analysis = self.pipeline.process_document(
            content=generic_text,
            filename="admin_memo.txt",
            workspace_id=101,
        )
        self.assertEqual(len(analysis.event_threads), 1)
        thread = analysis.event_threads[0]
        self.assertEqual(thread["action"], "skipped_no_event_evidence")
        self.assertFalse(thread["created_new_event"])
        self.assertIsNone(thread["event_id"])

    def test_event_gate_generic_document_with_ordinary_entities_but_no_incident_skips_threading(self):
        """Document with ordinary entities (DRDO, New Delhi) but no incident indicators skips event creation."""
        doc_text = (
            "The Defence Research and Development Organisation maintains research laboratories in New Delhi. "
            "These research facilities coordinate technological studies."
        )
        analysis = self.pipeline.process_document(
            content=doc_text,
            filename="org_overview.txt",
            workspace_id=101,
        )
        self.assertEqual(len(analysis.event_threads), 1)
        thread = analysis.event_threads[0]
        # Entities are extracted, but no incident/event occurs
        self.assertGreater(len(analysis.resolved_entities), 0)
        self.assertEqual(thread["action"], "skipped_no_event_evidence")
        self.assertFalse(thread["created_new_event"])
        self.assertIsNone(thread["event_id"])

    def test_event_gate_legitimate_defense_incident_triggers_threading(self):
        """Legitimate tactical incident with indicators triggers threading."""
        incident_text = (
            "Indian Air Force scrambled Su-30MKI fighters following radar detection near LAC "
            "after a suspected adversary reconnaissance intrusion."
        )
        analysis = self.pipeline.process_document(
            content=incident_text,
            filename="scramble_alert.txt",
            workspace_id=101,
        )
        self.assertEqual(len(analysis.event_threads), 1)
        thread = analysis.event_threads[0]
        self.assertIn(thread["action"], ("linked_existing", "created_new_cluster"))
        self.assertNotEqual(thread["action"], "skipped_no_event_evidence")

    def test_event_gate_incident_with_incomplete_entity_extraction_triggers_threading(self):
        """Incident with strong tactical indicators triggers threading even with partial entities."""
        incident_text = (
            "Heavy exchange of mortar fire and shelling reported across forward sectors along the Line of Control."
        )
        analysis = self.pipeline.process_document(
            content=incident_text,
            filename="shelling.txt",
            workspace_id=101,
        )
        self.assertEqual(len(analysis.event_threads), 1)
        thread = analysis.event_threads[0]
        self.assertIn(thread["action"], ("linked_existing", "created_new_cluster"))
        self.assertNotEqual(thread["action"], "skipped_no_event_evidence")

    def test_event_gate_empty_document_raises_empty_document_error(self):
        """Empty documents are blocked at extraction before event gate."""
        with self.assertRaises(EmptyDocumentError):
            self.pipeline.process_document(
                content="   ",
                filename="empty.txt",
                workspace_id=101,
            )


if __name__ == "__main__":
    unittest.main()
