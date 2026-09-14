export default async function handler(req, res) {
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

    const safeProducts = products.map(p => {
      const link = linkMap.get(String(p.id));
      return {
        id: p.id,
        title: p.title,
        price: p.price,
        image_url: p.image_url,
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