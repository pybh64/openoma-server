import { useState } from "react";
import { useAuthStore } from "@/stores/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { toast } from "sonner";

export default function LoginPage() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const [userId, setUserId] = useState("");
  const [tenantId, setTenantId] = useState("default");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      // When auth is enabled, this would hit a JWT/OAuth endpoint.
      // For now, set dev credentials directly.
      const uid = userId.trim() || "dev-user";
      setAuth(uid, tenantId.trim() || "default", ["admin"]);
      localStorage.setItem(
        "openoma-auth",
        JSON.stringify({ userId: uid, tenantId, roles: ["admin"] })
      );
      toast.success(`Logged in as ${uid}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
              className="h-6 w-6 text-primary"
            >
              <circle cx="12" cy="12" r="3" />
              <path d="M12 1v4m0 14v4M4.22 4.22l2.83 2.83m9.9 9.9l2.83 2.83M1 12h4m14 0h4M4.22 19.78l2.83-2.83m9.9-9.9l2.83-2.83" />
            </svg>
          </div>
          <CardTitle>OpenOMA</CardTitle>
          <CardDescription>Sign in to manage your operational processes</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <Label>User ID</Label>
              <Input
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                placeholder="dev-user"
                autoFocus
              />
            </div>
            <div>
              <Label>Tenant ID</Label>
              <Input
                value={tenantId}
                onChange={(e) => setTenantId(e.target.value)}
                placeholder="default"
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Signing in…" : "Sign In"}
            </Button>
            <p className="text-center text-[11px] text-muted-foreground">
              Auth is in development mode — any credentials will work
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
