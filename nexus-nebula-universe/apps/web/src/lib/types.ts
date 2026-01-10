export type Project = {
  id: string;
  title: string;
  kind: string;
  status: string;
  created_at: string;
  updated_at: string;
  prompt?: string;
  swarm_state?: any;
};

export type Listing = {
  id: string;
  title: string;
  description: string;
  price_cents: number;
  currency: string;
  status: string;
  created_at: string;
  artifact_id: string;
  seller_id: string;
};
