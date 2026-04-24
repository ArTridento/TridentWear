export const CATEGORY_GROUPS = [
  {
    title: "Fit Types",
    items: [
      { slug: "regular-fit", label: "Regular Fit T-Shirts", icon: "RF", copy: "Balanced everyday silhouettes." },
      { slug: "slim-fit", label: "Slim Fit T-Shirts", icon: "SF", copy: "Closer body shape with sharper lines." },
      { slug: "oversized-fit", label: "Oversized Fit T-Shirts", icon: "OF", copy: "Relaxed volume and dropped feel." },
      { slug: "boxy-fit", label: "Boxy Fit T-Shirts", icon: "BF", copy: "Wide body with compact length." },
    ],
  },
  {
    title: "Neck Types",
    items: [
      { slug: "round-neck", label: "Round Neck T-Shirts", icon: "RN", copy: "Classic crew neck construction." },
      { slug: "v-neck", label: "V-Neck T-Shirts", icon: "VN", copy: "Sharper neckline for layered fits." },
      { slug: "polo", label: "Polo T-Shirts", icon: "PL", copy: "Collared T-shirts with clean structure." },
    ],
  },
  {
    title: "Fabric Types",
    items: [
      { slug: "cotton", label: "Cotton T-Shirts", icon: "CT", copy: "Soft natural fabric with breathable comfort." },
      { slug: "polyester", label: "Polyester T-Shirts", icon: "PY", copy: "Lightweight feel with quick-dry utility." },
      { slug: "cotton-blend", label: "Cotton Blend T-Shirts", icon: "CB", copy: "Balanced softness and durability." },
    ],
  },
  {
    title: "Design Types",
    items: [
      { slug: "plain", label: "Plain T-Shirts", icon: "PL", copy: "Minimal base pieces for daily rotation." },
      { slug: "printed", label: "Printed T-Shirts", icon: "PR", copy: "Surface prints with lighter visual energy." },
      { slug: "graphic", label: "Graphic T-Shirts", icon: "GR", copy: "Statement graphics built for attention." },
      { slug: "typography", label: "Typography T-Shirts", icon: "TY", copy: "Text-led designs with bold placement." },
      { slug: "custom-print", label: "Custom Print T-Shirts", icon: "CP", copy: "Ready-to-personalize print bases." },
    ],
  },
  {
    title: "Special Types",
    items: [
      { slug: "drop-shoulder", label: "Drop Shoulder T-Shirts", icon: "DS", copy: "Relaxed shoulder seam and easy fall." },
      { slug: "full-sleeve", label: "Full Sleeve T-Shirts", icon: "FS", copy: "Long sleeve coverage for layering." },
      { slug: "crop", label: "Crop T-Shirts", icon: "CR", copy: "Shorter length with modern proportions." },
    ],
  },
];

export const CATEGORIES = CATEGORY_GROUPS.flatMap((group) =>
  group.items.map((item) => ({
    ...item,
    group: group.title,
  })),
);

export const SIZE_CHART = [
  { size: "S", chest: 38, length: 26 },
  { size: "M", chest: 40, length: 27 },
  { size: "L", chest: 42, length: 28 },
  { size: "XL", chest: 44, length: 29 },
  { size: "XXL", chest: 46, length: 30 },
];

const CATEGORY_LOOKUP = new Map(CATEGORIES.map((category) => [category.slug, category]));

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

export function getCategoryMeta(slug) {
  return CATEGORY_LOOKUP.get(slug) || null;
}

export function getProductCardTags(product) {
  const gsmLabel = product.gsm ? `${product.gsm} GSM` : null;
  return unique([product.fit_type, product.material, gsmLabel]);
}

export function normalizeProduct(product) {
  const fitType = product.fit_type || "Regular Fit";
  const neckType = product.neck_type || "Round Neck";
  const material = product.material || "Cotton";
  const gsm = Number(product.gsm || 220);
  const designType = product.design_type || "Plain";
  const specialType = product.special_type || "";
  const categories = unique(
    Array.isArray(product.categories) && product.categories.length
      ? product.categories
      : [
          fitType.toLowerCase().replaceAll(" ", "-"),
          neckType.toLowerCase().replaceAll(" ", "-"),
          material.toLowerCase().replaceAll(" ", "-"),
          designType.toLowerCase().replaceAll(" ", "-"),
          specialType.toLowerCase().replaceAll(" ", "-"),
        ],
  );

  return {
    ...product,
    category: product.category || "tshirt",
    categories,
    fit_type: fitType,
    neck_type: neckType,
    material,
    gsm,
    design_type: designType,
    special_type: specialType,
    sizes: Array.isArray(product.sizes) && product.sizes.length ? product.sizes : ["S", "M", "L", "XL", "XXL"],
    card_tags: getProductCardTags({ fit_type: fitType, material, gsm }),
    category_labels: categories.map((slug) => getCategoryMeta(slug)?.label).filter(Boolean),
  };
}

export function matchesCategory(product, slug) {
  if (!slug || slug === "all") {
    return true;
  }
  return normalizeProduct(product).categories.includes(slug);
}

export function relatedProducts(products, targetProduct) {
  const target = normalizeProduct(targetProduct);
  const categorySet = new Set(target.categories);

  return products
    .map(normalizeProduct)
    .filter((product) => product.id !== target.id)
    .map((product) => ({
      product,
      score: product.categories.filter((category) => categorySet.has(category)).length,
    }))
    .filter((entry) => entry.score > 0)
    .sort((left, right) => right.score - left.score || left.product.price - right.product.price)
    .map((entry) => entry.product);
}
