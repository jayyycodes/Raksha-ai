/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async redirects() {
    return [
      {
        source: '/',
        destination: '/articles',
        permanent: false,
      },
    ];
  },
};

module.exports = nextConfig;
