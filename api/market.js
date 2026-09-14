export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Accept, Content-Type');

  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_PUBLISHABLE_KEY;

  if (!url || !key) {
    return res.status(500).json({ error: 'Supabase environment is not configured' });
  }

  try {
    const headers = {
      apikey: key,
      Authorization: 'Bearer ' + key,
      Accept: 'application/json'
    };

    const [productsResponse, linksResponse] = await Promise.all([
      fetch(url + '/rest/v1/products?select=id,title,price,image_url&order=id.desc', { headers }),
      fetch(url + '/rest/v1/affiliate_links?select=product_id,short_url,platform', { headers })
    ]);

    if (!productsResponse.ok || !linksResponse.ok) {
      return res.status(502).json({ error: 'Supabase catalog unavailable' });
    }

    const [products, links] = await Promise.all([
      productsResponse.json(),
      linksResponse.json()
    ]);

    const linkMap = new Map();
    for (const link of links) {
      if (link.product_id != null && link.short_url && !linkMap.has(String(link.product_id))) {
        linkMap.set(String(link.product_id), link);
      }
    }

    const looksLikePlaceholder = (value) => !value || /susercontent\.com\/file\/vn-11134207-7r98o-lvmhwp0f8n2j64/i.test(value);

    async function resolveOgImage(url) {
      if (!url) return '';
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 4500);
      try {
        const response = await fetch(url, {
          redirect: 'follow',
          signal: controller.signal,
          headers: { 'User-Agent': 'Mozilla/5.0 Market-Deal/1.0' }
        });
        if (!response.ok) return '';
        const html = await response.text();
        const patterns = [
          /<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']+)["']/i,
          /<meta[^>]+content=["']([^"']+)["'][^>]+property=["']og:image["']/i,
          /<meta[^>]+name=["']twitter:image["'][^>]+content=["']([^"']+)["']/i
        ];
        for (const pattern of patterns) {
          const match = html.match(pattern);
          if (match?.[1]) return match[1].replace(/&amp;/g, '&');
        }
        return '';
      } catch (_) {
        return '';
      } finally {
        clearTimeout(timer);
      }
    }

    const resolvedImages = new Map();
    const candidates = products.map(p => {
      const link = linkMap.get(String(p.id));
      return { p, link };
    }).filter(({ p, link }) => looksLikePlaceholder(p.image_url) && link?.short_url);

    // Resolve real product images from the affiliate destination when the DB contains the old shared placeholder.
    for (let i = 0; i < candidates.length; i += 6) {
      const batch = candidates.slice(i, i + 6);
      const results = await Promise.all(batch.map(async ({ p, link }) => [
        String(p.id),
        await resolveOgImage(link.short_url)
      ]));
      for (const [id, image] of results) if (image) resolvedImages.set(id, image);
    }

    const safeProducts = products.map(p => {
      const link = linkMap.get(String(p.id));
      const resolved = resolvedImages.get(String(p.id));
      return {
        id: p.id,
        title: p.title,
        price: p.price,
        image_url: resolved || p.image_url || '',
        affiliate_url: link?.short_url || '',
        platform: link?.platform || 'Affiliate'
      };
    });

    res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=300');
    return res.status(200).json({ products: safeProducts });
  } catch (error) {
    console.error('Market API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}