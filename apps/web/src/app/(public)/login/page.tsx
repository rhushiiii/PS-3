import { Suspense } from "react";
import { Login } from "@/features/auth/login";

export default function LoginPage() {
  return (
    <Suspense>
      <Login />
    </Suspense>
  );
}
