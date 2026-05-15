export type AuthUser = {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
};

export type AuthOrganization = {
  id: string;
  name: string;
  slug: string;
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};

export type AuthSession = {
  user: AuthUser;
  organization: AuthOrganization;
  membership_status: string;
  role: string;
  tokens: TokenPair;
};
