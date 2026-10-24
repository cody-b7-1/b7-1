import { Link } from "react-router";
import { AlertCircle } from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";

export type AuthServerError = {
  message: string;
  linkText?: string;
  linkTo?: string;
};

interface AuthErrorAlertProps {
  error: AuthServerError | null;
}

export function AuthErrorAlert({ error }: AuthErrorAlertProps) {
  if (!error) return null;

  return (
    <Alert variant="destructive">
      <AlertCircle className="size-4" />
      <AlertDescription className="flex flex-col gap-1.5">
        <span className="whitespace-pre-line">{error.message}</span>
        {error.linkTo && error.linkText && (
          <Link
            to={error.linkTo}
            className="font-medium underline underline-offset-4 hover:opacity-80"
          >
            {error.linkText}
          </Link>
        )}
      </AlertDescription>
    </Alert>
  );
}
