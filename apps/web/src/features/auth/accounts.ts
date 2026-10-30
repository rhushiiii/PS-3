export type DemoAccount = {
  alias: string;
  label: string;
  role: string;
  monogram: string;
};

export const demoAccounts: DemoAccount[] = [
  {
    alias: "cedar_admin",
    label: "Cedar Institute",
    role: "Institution administrator",
    monogram: "CE",
  },
  {
    alias: "maple_admin",
    label: "Maple Institute",
    role: "Institution administrator",
    monogram: "MA",
  },
  {
    alias: "willow_admin",
    label: "Willow Institute",
    role: "Institution administrator",
    monogram: "WI",
  },
  {
    alias: "demo_officer",
    label: "Admissions Officer",
    role: "Institution review access",
    monogram: "OF",
  },
  {
    alias: "demo_manager",
    label: "Admissions Manager",
    role: "Institution metadata access",
    monogram: "MG",
  },
  {
    alias: "demo_officer_2",
    label: "Admissions Officer 2",
    role: "Institution review access",
    monogram: "O2",
  },
  {
    alias: "demo_verifier",
    label: "Credential Verifier",
    role: "Credential verification access",
    monogram: "VF",
  },
];
