import { useState, useCallback } from "react";
import { User, Key, Shield, ShieldCheck, ShieldOff } from "lucide-react";
import { toast } from "sonner";
import api, { ApiError } from "@/api/client";
import type { SingleResponse } from "@/api/types";
import { useAuth } from "@/auth/AuthContext";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

type MfaSetupResponse = {
  secret: string;
  provisioning_uri: string;
};

function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return "—";
  }
}

export function ProfilePage() {
  const { user, refreshUser } = useAuth();

  const [changePassword, setChangePassword] = useState({
    current: "",
    new: "",
    confirm: "",
  });
  const [changePasswordSubmitting, setChangePasswordSubmitting] = useState(false);
  const [changePasswordError, setChangePasswordError] = useState<string | null>(null);

  const [mfaSetup, setMfaSetup] = useState<MfaSetupResponse | null>(null);
  const [mfaSetupCode, setMfaSetupCode] = useState("");
  const [mfaSetupSubmitting, setMfaSetupSubmitting] = useState(false);
  const [mfaSetupError, setMfaSetupError] = useState<string | null>(null);
  const [showMfaSetupDialog, setShowMfaSetupDialog] = useState(false);

  const [mfaDisablePassword, setMfaDisablePassword] = useState("");
  const [mfaDisableCode, setMfaDisableCode] = useState("");
  const [showMfaDisableDialog, setShowMfaDisableDialog] = useState(false);
  const [mfaDisableSubmitting, setMfaDisableSubmitting] = useState(false);
  const [mfaDisableError, setMfaDisableError] = useState<string | null>(null);

  const handleChangePassword = useCallback(
    async (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      setChangePasswordError(null);
      if (changePassword.new !== changePassword.confirm) {
        setChangePasswordError("New password and confirmation do not match");
        return;
      }
      if (changePassword.new.length < 8) {
        setChangePasswordError("Password must be at least 8 characters");
        return;
      }
      setChangePasswordSubmitting(true);
      try {
        await api.post("/auth/change-password", {
          current_password: changePassword.current,
          new_password: changePassword.new,
        });
        setChangePassword({ current: "", new: "", confirm: "" });
        toast.success("Password changed successfully.");
      } catch (err) {
        const msg =
          err instanceof ApiError ? err.message : "Failed to change password";
        setChangePasswordError(msg);
      } finally {
        setChangePasswordSubmitting(false);
      }
    },
    [changePassword],
  );

  const handleStartMfaSetup = useCallback(async () => {
    setMfaSetupError(null);
    setMfaSetup(null);
    setShowMfaSetupDialog(true);
    try {
      const res = await api.get<SingleResponse<MfaSetupResponse>>("/auth/mfa/setup");
      setMfaSetup(res.data.data);
    } catch (err) {
      setMfaSetupError(
        err instanceof ApiError ? err.message : "Failed to start MFA setup",
      );
      setShowMfaSetupDialog(false);
    }
  }, []);

  const handleConfirmMfaSetup = useCallback(async () => {
    if (!mfaSetupCode.trim()) return;
    setMfaSetupError(null);
    setMfaSetupSubmitting(true);
    try {
      await api.post("/auth/mfa/confirm", { code: mfaSetupCode.trim() });
      await refreshUser();
      setShowMfaSetupDialog(false);
      setMfaSetup(null);
      setMfaSetupCode("");
      toast.success("MFA enabled successfully.");
    } catch (err) {
      setMfaSetupError(
        err instanceof ApiError ? err.message : "Invalid verification code",
      );
    } finally {
      setMfaSetupSubmitting(false);
    }
  }, [mfaSetupCode, refreshUser]);

  const handleCloseMfaSetup = useCallback(() => {
    setShowMfaSetupDialog(false);
    setMfaSetup(null);
    setMfaSetupCode("");
    setMfaSetupError(null);
  }, []);

  const handleConfirmMfaDisable = useCallback(async () => {
    if (!mfaDisablePassword && !mfaDisableCode.trim()) {
      setMfaDisableError("Enter your password or TOTP code");
      return;
    }
    setMfaDisableError(null);
    setMfaDisableSubmitting(true);
    try {
      await api.post("/auth/mfa/disable", {
        password: mfaDisablePassword || undefined,
        code: mfaDisableCode.trim() || undefined,
      });
      await refreshUser();
      setShowMfaDisableDialog(false);
      setMfaDisablePassword("");
      setMfaDisableCode("");
      toast.success("MFA disabled successfully.");
    } catch (err) {
      setMfaDisableError(
        err instanceof ApiError ? err.message : "Failed to disable MFA",
      );
    } finally {
      setMfaDisableSubmitting(false);
    }
  }, [mfaDisablePassword, mfaDisableCode, refreshUser]);

  const handleCloseMfaDisable = useCallback(() => {
    setShowMfaDisableDialog(false);
    setMfaDisablePassword("");
    setMfaDisableCode("");
    setMfaDisableError(null);
  }, []);

  if (!user) return null;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
          Profile
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          View your account info and manage password and MFA.
        </p>
      </div>

      <div className="space-y-6">
        {/* Account info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="size-5" />
              Account info
            </CardTitle>
            <CardDescription>Your account details (read-only)</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <Label className="text-muted-foreground">Email</Label>
                <p className="mt-1 font-medium">{user.email}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Role</Label>
                <p className="mt-1 font-medium">{user.role_name ?? "—"}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">MFA status</Label>
                <div className="mt-1">
                  {user.mfa_enabled ? (
                    <Badge variant="success" className="gap-1">
                      <ShieldCheck className="size-4" />
                      Enabled
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="gap-1">
                      <ShieldOff className="size-4" />
                      Disabled
                    </Badge>
                  )}
                </div>
              </div>
              <div>
                <Label className="text-muted-foreground">Account created</Label>
                <p className="mt-1 font-medium">{formatDate(user.created_at)}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Last login</Label>
                <p className="mt-1 font-medium">{formatDate(user.last_login_at)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Change password */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="size-5" />
              Change password
            </CardTitle>
            <CardDescription>
              Update your password. Use at least 8 characters.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleChangePassword} className="space-y-4">
              {changePasswordError && (
                <p className="text-sm text-destructive">{changePasswordError}</p>
              )}
              <div className="space-y-2">
                <Label htmlFor="current-password">Current password</Label>
                <Input
                  id="current-password"
                  type="password"
                  required
                  value={changePassword.current}
                  onChange={(e) =>
                    setChangePassword((p) => ({ ...p, current: e.target.value }))
                  }
                  placeholder="••••••••"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-password">New password</Label>
                <Input
                  id="new-password"
                  type="password"
                  required
                  value={changePassword.new}
                  onChange={(e) =>
                    setChangePassword((p) => ({ ...p, new: e.target.value }))
                  }
                  placeholder="••••••••"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm-password">Confirm new password</Label>
                <Input
                  id="confirm-password"
                  type="password"
                  required
                  value={changePassword.confirm}
                  onChange={(e) =>
                    setChangePassword((p) => ({ ...p, confirm: e.target.value }))
                  }
                  placeholder="••••••••"
                />
              </div>
              <Button type="submit" disabled={changePasswordSubmitting}>
                {changePasswordSubmitting ? "Changing…" : "Change password"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* MFA management */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="size-5" />
              Two-factor authentication
            </CardTitle>
            <CardDescription>
              Add an extra layer of security with an authenticator app.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {user.mfa_enabled ? (
              <div className="flex items-center justify-between gap-4">
                <p className="text-sm text-muted-foreground">
                  MFA is enabled. Use an authenticator app to sign in.
                </p>
                <Button
                  variant="outline"
                  className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                  onClick={() => setShowMfaDisableDialog(true)}
                >
                  Disable MFA
                </Button>
              </div>
            ) : (
              <div className="flex items-center justify-between gap-4">
                <p className="text-sm text-muted-foreground">
                  MFA is not enabled. Enable it to secure your account.
                </p>
                <Button onClick={handleStartMfaSetup}>Enable MFA</Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* MFA setup dialog */}
      <Dialog open={showMfaSetupDialog} onOpenChange={(open) => !open && handleCloseMfaSetup()}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Enable MFA</DialogTitle>
            <DialogDescription>
              Scan the QR code with your authenticator app (Google Authenticator, Authy, etc.) or
              enter the secret manually. Then enter the 6-digit code to verify.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {mfaSetupError && (
              <p className="text-sm text-destructive">{mfaSetupError}</p>
            )}
            {mfaSetup && (
              <>
                <div className="flex justify-center">
                  <img
                    src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(mfaSetup.provisioning_uri)}`}
                    alt="MFA QR code"
                    width={200}
                    height={200}
                    className="rounded border"
                  />
                </div>
                <p className="text-center text-xs text-muted-foreground">
                  Or enter manually: <code className="break-all">{mfaSetup.secret}</code>
                </p>
                <div className="space-y-2">
                  <Label htmlFor="mfa-code">Verification code</Label>
                  <Input
                    id="mfa-code"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    maxLength={6}
                    placeholder="000000"
                    value={mfaSetupCode}
                    onChange={(e) =>
                      setMfaSetupCode(e.target.value.replace(/\D/g, ""))
                    }
                  />
                </div>
              </>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={handleCloseMfaSetup}>
              Cancel
            </Button>
            <Button
              onClick={handleConfirmMfaSetup}
              disabled={!mfaSetup || mfaSetupCode.length !== 6 || mfaSetupSubmitting}
            >
              {mfaSetupSubmitting ? "Verifying…" : "Verify and enable"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* MFA disable dialog */}
      <Dialog
        open={showMfaDisableDialog}
        onOpenChange={(open) => !open && handleCloseMfaDisable()}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Disable MFA</DialogTitle>
            <DialogDescription>
              Enter your password or current TOTP code to confirm.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {mfaDisableError && (
              <p className="text-sm text-destructive">{mfaDisableError}</p>
            )}
            <div className="space-y-2">
              <Label htmlFor="mfa-disable-password">Password</Label>
              <Input
                id="mfa-disable-password"
                type="password"
                value={mfaDisablePassword}
                onChange={(e) => setMfaDisablePassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
            <p className="text-center text-sm text-muted-foreground">— or —</p>
            <div className="space-y-2">
              <Label htmlFor="mfa-disable-code">TOTP code</Label>
              <Input
                id="mfa-disable-code"
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                value={mfaDisableCode}
                onChange={(e) =>
                  setMfaDisableCode(e.target.value.replace(/\D/g, ""))
                }
                placeholder="000000"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={handleCloseMfaDisable}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleConfirmMfaDisable}
              disabled={
                (!mfaDisablePassword && !mfaDisableCode.trim()) ||
                mfaDisableSubmitting
              }
            >
              {mfaDisableSubmitting ? "Disabling…" : "Disable MFA"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
