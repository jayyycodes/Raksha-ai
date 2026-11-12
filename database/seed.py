"""
Seeds the sources table and high-trust official entity designation baselines.
Run: python -m database.seed
"""
from sqlalchemy import text
from common.db import get_db
from common.logger import get_logger
from scraper.sources import RSS_SOURCES

logger = get_logger(__name__)

# Authoritative public official lists & designations (PIB / MoD / UN Security Council 1267 / SIPRI)
# Every entry carries explicit official source attribution per Safeguard Rule #2.
OFFICIAL_DESIGNATION_FACTS = [
    {
        "entity_name": "Indian Army",
        "entity_type": "ORGANISATION",
        "primary_ring": 1,
        "aliases": ["IA", "Indian Army", "Army"],
        "facts": [
            (
                "Designated land-based branch of the Indian Armed Forces under the Ministry of Defence (MoD).",
                "Ministry of Defence / PIB Official Portal",
                1.0,
            ),
            (
                "Northern Command (Udhampur) oversees operational readiness across Ladakh and Jammu & Kashmir sectors.",
                "PIB India Official Release",
                0.98,
            ),
        ],
    },
    {
        "entity_name": "Indian Air Force",
        "entity_type": "ORGANISATION",
        "primary_ring": 1,
        "aliases": ["IAF", "Indian Air Force", "Air Force"],
        "facts": [
            (
                "Air arm of the Indian Armed Forces responsible for airspace defence and integrated air command.",
                "Ministry of Defence / PIB Official Portal",
                1.0,
            ),
        ],
    },
    {
        "entity_name": "DRDO",
        "entity_type": "ORGANISATION",
        "primary_ring": 1,
        "aliases": ["DRDO", "Defence Research and Development Organisation"],
        "facts": [
            (
                "Premier R&D agency under the Department of Defence Research and Development, Ministry of Defence.",
                "PIB India / DRDO Official Charter",
                1.0,
            ),
        ],
    },
    {
        "entity_name": "General Upendra Dwivedi",
        "entity_type": "PERSON",
        "primary_ring": 1,
        "aliases": ["Upendra Dwivedi", "Gen Upendra Dwivedi", "COAS", "Army Chief"],
        "facts": [
            (
                "Officially appointed Chief of the Army Staff (COAS) of the Indian Army per Ministry of Defence notification.",
                "PIB India / Ministry of Defence Notification",
                1.0,
            ),
        ],
    },
    {
        "entity_name": "Jaish-e-Mohammed",
        "entity_type": "ORGANISATION",
        "primary_ring": 2,
        "aliases": ["JeM", "Jaish-e-Mohammed", "Jaish-e-Mohammad"],
        "facts": [
            (
                "Listed under United Nations Security Council Resolution 1267 / 1989 / 2253 Sanctions List (QDe.019) and proscribed under India's UAPA First Schedule.",
                "UN Security Council 1267 Sanctions List / MHA Official Notification",
                1.0,
            ),
        ],
    },
    {
        "entity_name": "Lashkar-e-Taiba",
        "entity_type": "ORGANISATION",
        "primary_ring": 2,
        "aliases": ["LeT", "Lashkar-e-Taiba", "Lashkar-e-Tayyiba"],
        "facts": [
            (
                "Listed under United Nations Security Council Resolution 1267 Sanctions List (QDe.118) and proscribed under India's UAPA First Schedule.",
                "UN Security Council 1267 Sanctions List / MHA Official Notification",
                1.0,
            ),
        ],
    },
    {
        "entity_name": "PLA Ground Force",
        "entity_type": "ORGANISATION",
        "primary_ring": 2,
        "aliases": ["PLA", "PLA Ground Force", "People's Liberation Army"],
        "facts": [
            (
                "Official land warfare branch of the People's Liberation Army under the Central Military Commission (CMC).",
                "PRC Ministry of National Defense / Public Official White Paper",
                0.98,
            ),
        ],
    },
    {
        "entity_name": "Western Theater Command",
        "entity_type": "ORGANISATION",
        "primary_ring": 2,
        "aliases": ["WTC", "Western Theater Command", "Western Theatre Command"],
        "facts": [
            (
                "Geographic theater command of the PLA headquartered in Chengdu covering Xinjiang and Tibet frontier sectors.",
                "Public Defence White Papers / IISS Military Balance",
                0.95,
            ),
        ],
    },
]


def seed_sources():
    with get_db() as db:
        inserted = 0
        for source in RSS_SOURCES:
            result = db.execute(
                text("""
                    INSERT INTO sources (name, url, rss_url, ring, country, language)
                    VALUES (:name, :url, :rss_url, :ring, :country, :language)
                    ON CONFLICT (name) DO UPDATE SET
                        url = EXCLUDED.url,
                        rss_url = EXCLUDED.rss_url,
                        ring = EXCLUDED.ring,
                        country = EXCLUDED.country,
                        language = EXCLUDED.language
                """),
                source,
            )
            if result.rowcount:
                inserted += 1
        logger.info(
            f"Seeded / updated {inserted} sources "
            f"({len(RSS_SOURCES)} total in registry)"
        )


def seed_official_designations():
    """Seed high-trust official entity baselines and attributed designation facts."""
    facts_added = 0
    with get_db() as db:
        for entry in OFFICIAL_DESIGNATION_FACTS:
            node_row = db.execute(
                text("""
                    INSERT INTO entity_nodes (
                        name, entity_type, aliases, primary_ring, mention_count, source_count, is_profile
                    ) VALUES (
                        :name, :etype, :aliases, :ring, 5, 3, TRUE
                    )
                    ON CONFLICT (name, entity_type) DO UPDATE SET
                        aliases = EXCLUDED.aliases,
                        is_profile = TRUE
                    RETURNING id
                """),
                {
                    "name": entry["entity_name"],
                    "etype": entry["entity_type"],
                    "aliases": entry["aliases"],
                    "ring": entry["primary_ring"],
                },
            ).fetchone()
            entity_id = int(node_row.id)

            for fact_text, source_name, conf in entry["facts"]:
                exists = db.execute(
                    text("""
                        SELECT 1 FROM profile_facts
                        WHERE entity_id = :eid AND fact = :fact
                        LIMIT 1
                    """),
                    {"eid": entity_id, "fact": fact_text},
                ).fetchone()
                if not exists:
                    db.execute(
                        text("""
                            INSERT INTO profile_facts (
                                entity_id, fact, claim_status, source_name, confidence
                            ) VALUES (
                                :eid, :fact, 'official_designation', :source_name, :conf
                            )
                        """),
                        {
                            "eid": entity_id,
                            "fact": fact_text,
                            "source_name": source_name,
                            "conf": conf,
                        },
                    )
                    facts_added += 1

    logger.info(f"Seeded {facts_added} attributed official designation fact(s).")


def seed_all():
    seed_sources()
    seed_official_designations()


if __name__ == "__main__":
    seed_all()
