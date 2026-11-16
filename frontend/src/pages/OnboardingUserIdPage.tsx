import { Link } from "react-router-dom";

import { useAuthStore } from "../store/authStore";

export function OnboardingUserIdPage() {
  const userId = useAuthStore((s) => s.pendingUserId);

  return (
    <div className="mx-auto mt-20 max-w-lg rounded-xl border border-sky-100 bg-white p-6">
      <h1 className="font-heading text-2xl font-bold">Seu user_id MindEdu</h1>
      <p className="mt-2 text-sm text-ink/70">sua conta foi criada com sucesso, seu id e {userId ?? "(indisponivel)"}, aguarde a aprovação de seu cadastro</p>
      <div className="mt-4 rounded-lg bg-mint p-4 text-center font-mono text-xl font-semibold">{userId ?? "(indisponivel)"}</div>
      <Link to="/login" className="mt-4 inline-block rounded bg-ink px-4 py-2 text-white">
        Ir para login
      </Link>
    </div>
  );
}
