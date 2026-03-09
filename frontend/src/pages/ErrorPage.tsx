import { useRouteError, isRouteErrorResponse, Link } from "react-router";

function ErrorLayout({
  is404,
  title,
  message,
  errorDetails,
}: {
  is404: boolean;
  title: string;
  message: string;
  errorDetails?: string;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-navy-950 via-navy-800 to-navy-700 px-4">
      <div className="w-full max-w-lg text-center">
        <div className="mb-8">
          <div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-2xl bg-white/10 text-6xl font-bold text-white">
            {is404 ? "404" : "!"}
          </div>
          <h1 className="text-4xl font-bold text-white tracking-tight">
            {title}
          </h1>
          <p className="mt-3 text-lg text-mint-300">{message}</p>
        </div>

        <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <Link
            to="/"
            className="inline-flex items-center gap-2 rounded-lg bg-white px-6 py-3 font-medium text-navy-800 shadow-lg transition-all hover:bg-mint-100 hover:shadow-xl"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
              />
            </svg>
            Back to home
          </Link>
          <Link
            to="/login"
            className="inline-flex items-center rounded-lg border-2 border-white/30 px-6 py-3 font-medium text-white transition-all hover:border-white/50 hover:bg-white/10"
          >
            Sign in
          </Link>
        </div>

        {errorDetails && (
          <div className="mt-12 rounded-xl bg-black/20 p-4 text-left">
            <p className="mb-2 text-xs font-medium uppercase tracking-wider text-mint-400">
              Error details (dev only)
            </p>
            <pre className="overflow-x-auto text-sm text-mint-200">
              {errorDetails}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

/** Used as errorElement - handles both 404 and other errors */
export function ErrorPage() {
  const error = useRouteError();
  const is404 = isRouteErrorResponse(error) && error.status === 404;
  const title = is404 ? "Page not found" : "Something went wrong";
  const message = is404
    ? "The page you're looking for doesn't exist or has been moved."
    : "An unexpected error occurred. Please try again.";
  const errorDetails =
    !is404 &&
    (import.meta as { env?: { DEV?: boolean } }).env?.DEV &&
    error instanceof Error
      ? error.message
      : undefined;

  return (
    <ErrorLayout
      is404={is404}
      title={title}
      message={message}
      errorDetails={errorDetails}
    />
  );
}

/** Used as catch-all route - always 404 */
export function NotFoundPage() {
  return (
    <ErrorLayout
      is404
      title="Page not found"
      message="The page you're looking for doesn't exist or has been moved."
    />
  );
}
