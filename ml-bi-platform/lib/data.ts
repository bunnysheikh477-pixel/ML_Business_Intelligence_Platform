export type SaleRow = { date: string; product: string; region: string; revenue: number; cost: number; orders: number };
export const sampleSales: SaleRow[] = [
  { date: '2025-01-05', product: 'Studio Headphones', region: 'North America', revenue: 18200, cost: 10920, orders: 146 },
  { date: '2025-01-12', product: 'Studio Headphones', region: 'Europe', revenue: 14600, cost: 8760, orders: 119 },
  { date: '2025-02-02', product: 'Smart Speaker', region: 'Asia Pacific', revenue: 22300, cost: 13380, orders: 201 },
  { date: '2025-02-16', product: 'Wireless Earbuds', region: 'North America', revenue: 19800, cost: 9900, orders: 238 },
  { date: '2025-03-02', product: 'Smart Speaker', region: 'Europe', revenue: 25700, cost: 15420, orders: 229 },
  { date: '2025-03-16', product: 'Wireless Earbuds', region: 'Asia Pacific', revenue: 24100, cost: 12050, orders: 286 },
  { date: '2025-04-06', product: 'Studio Headphones', region: 'North America', revenue: 26900, cost: 16140, orders: 211 },
  { date: '2025-04-20', product: 'Smart Speaker', region: 'Asia Pacific', revenue: 29400, cost: 17640, orders: 263 },
  { date: '2025-05-04', product: 'Wireless Earbuds', region: 'Europe', revenue: 31800, cost: 15900, orders: 348 },
  { date: '2025-05-18', product: 'Studio Headphones', region: 'North America', revenue: 33600, cost: 20160, orders: 254 },
  { date: '2025-06-01', product: 'Smart Speaker', region: 'Europe', revenue: 36200, cost: 21720, orders: 321 },
  { date: '2025-06-15', product: 'Wireless Earbuds', region: 'Asia Pacific', revenue: 38900, cost: 19450, orders: 402 },
  { date: '2025-07-06', product: 'Studio Headphones', region: 'Europe', revenue: 35100, cost: 21060, orders: 278 },
  { date: '2025-07-20', product: 'Smart Speaker', region: 'North America', revenue: 40700, cost: 24420, orders: 365 },
  { date: '2025-08-03', product: 'Wireless Earbuds', region: 'Europe', revenue: 43200, cost: 21600, orders: 447 },
  { date: '2025-08-17', product: 'Smart Speaker', region: 'Asia Pacific', revenue: 46100, cost: 27660, orders: 418 },
  { date: '2025-09-07', product: 'Studio Headphones', region: 'North America', revenue: 47800, cost: 28680, orders: 359 },
  { date: '2025-09-21', product: 'Wireless Earbuds', region: 'Asia Pacific', revenue: 49300, cost: 24650, orders: 492 },
  { date: '2025-10-05', product: 'Smart Speaker', region: 'Europe', revenue: 52700, cost: 31620, orders: 471 },
  { date: '2025-10-19', product: 'Wireless Earbuds', region: 'North America', revenue: 54900, cost: 27450, orders: 521 },
  { date: '2025-11-02', product: 'Studio Headphones', region: 'Asia Pacific', revenue: 56800, cost: 34080, orders: 432 },
  { date: '2025-11-16', product: 'Smart Speaker', region: 'North America', revenue: 58700, cost: 35220, orders: 514 },
  { date: '2025-12-07', product: 'Wireless Earbuds', region: 'Europe', revenue: 62400, cost: 31200, orders: 608 },
  { date: '2025-12-21', product: 'Smart Speaker', region: 'Asia Pacific', revenue: 68300, cost: 40980, orders: 629 }
];
export const money = (n: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n);
