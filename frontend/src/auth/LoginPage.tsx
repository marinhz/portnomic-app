import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router";
import { useAuth } from "./AuthContext";

export function LoginPage() {
  const { login, completeMfa, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [mfaRequired, setMfaRequired] = useState(false);
  const [mfaToken, setMfaToken] = useState("");
  const [mfaCode, setMfaCode] = useState("");

  const from = (location.state as { from?: string } | null)?.from ?? "/";

  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  async function handleLogin(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const result = await login(email, password);
    setIsSubmitting(false);

    if ("requiresMfa" in result) {
      setMfaRequired(true);
      setMfaToken(result.mfaToken);
    } else if (result.success) {
      navigate(from, { replace: true });
    } else {
      setError(result.error);
    }
  }

  async function handleMfa(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const result = await completeMfa(mfaToken, mfaCode);
    setIsSubmitting(false);

    if (result.success) {
      navigate(from, { replace: true });
    } else {
      setError("error" in result ? result.error : "Verification failed");
    }
  }

  const inputClass =
    "w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-500 transition-colors focus:border-mint-500 focus:outline-none focus:ring-2 focus:ring-mint-500/20";

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-navy-950 via-navy-800 to-navy-700 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <img
            src="/Portnomic.svg"
            alt="Portnomic"
            className="mx-auto mb-4 h-14 w-14 rounded-xl object-contain"
          />
          <h1 className="text-3xl font-bold text-white">
            Portnomic
          </h1>
          <p className="mt-2 text-mint-300">Maritime Agency Platform</p>
        </div>

        <div className="rounded-xl bg-white p-8 shadow-2xl">
          {!mfaRequired ? (
            <>
              <h2 className="mb-6 text-center text-xl font-semibold text-slate-800">
                Sign in to your account
              </h2>

              {error && (
                <div
                  role="alert"
                  className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-800"
                >
                  {error}
                </div>
              )}

              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label
                    htmlFor="email"
                    className="mb-1 block text-sm font-medium text-slate-700"
                  >
                    Email
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setEmail(e.target.value)
                    }
                    required
                    className={inputClass}
                    placeholder="you@company.com"
                  />
                </div>

                <div>
                  <label
                    htmlFor="password"
                    className="mb-1 block text-sm font-medium text-slate-700"
                  >
                    Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setPassword(e.target.value)
                    }
                    required
                    className={inputClass}
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
                >
                  {isSubmitting ? "Signing in..." : "Sign in"}
                </button>
              </form>
            </>
          ) : (
            <>
              <h2 className="mb-2 text-center text-xl font-semibold text-slate-800">
                Two-Factor Authentication
              </h2>
              <p className="mb-6 text-center text-sm text-slate-500">
                Enter the code from your authenticator app
              </p>

              {error && (
                <div
                  role="alert"
                  className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-800"
                >
                  {error}
                </div>
              )}

              <form onSubmit={handleMfa} className="space-y-4">
                <div>
                  <label
                    htmlFor="mfa-code"
                    className="mb-1 block text-sm font-medium text-slate-700"
                  >
                    Verification Code
                  </label>
                  <input
                    id="mfa-code"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    maxLength={6}
                    value={mfaCode}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setMfaCode(e.target.value)
                    }
                    required
                    className={`${inputClass} text-center text-lg tracking-widest`}
                    placeholder="000000"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
                >
                  {isSubmitting ? "Verifying..." : "Verify"}
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setMfaRequired(false);
                    setError(null);
                  }}
                  className="w-full text-sm text-mint-500 hover:text-mint-400"
                >
                  Back to login
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
