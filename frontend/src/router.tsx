import { createBrowserRouter, Outlet } from "react-router";
import { AuthProvider } from "./auth/AuthContext";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { LoginPage } from "./auth/LoginPage";
import { ErrorPage, NotFoundPage } from "./pages/ErrorPage";
import { AppLayout } from "./layout/AppLayout";
import { Dashboard } from "./pages/Dashboard";
import { VesselList } from "./pages/vessels/VesselList";
import { VesselForm } from "./pages/vessels/VesselForm";
import { VesselDetail } from "./pages/vessels/VesselDetail";
import { PortCallList } from "./pages/port-calls/PortCallList";
import { PortCallForm } from "./pages/port-calls/PortCallForm";
import { PortCallWizard } from "./pages/port-calls/PortCallWizard";
import { PortCallDetail } from "./pages/port-calls/PortCallDetail";
import { PortCallAudit } from "./pages/port-calls/PortCallAudit";
import { PortCallDocuments } from "./pages/port-calls/PortCallDocuments";
import {
  portCallDetailLoader,
  portCallAuditLoader,
  portCallDocumentsLoader,
} from "./pages/port-calls/loaders";
import { DAList } from "./pages/da/DAList";
import { DADetail } from "./pages/da/DADetail";
import { DAGenerate } from "./pages/da/DAGenerate";
import { EmailList } from "./pages/emails/EmailList";
import { EmailDetail } from "./pages/emails/EmailDetail";
import { UserList } from "./pages/admin/UserList";
import { UserForm } from "./pages/admin/UserForm";
import { RoleList } from "./pages/admin/RoleList";
import { RoleForm } from "./pages/admin/RoleForm";
import { CompanyList } from "./pages/platform/CompanyList";
import { CompanyForm } from "./pages/platform/CompanyForm";
import { CompanyDetail } from "./pages/platform/CompanyDetail";
import { IntegrationsPage } from "./pages/settings/IntegrationsPage";
import { Billing } from "./pages/settings/Billing";
import { AISettingsPage } from "./pages/settings/AISettingsPage";
import { ProfilePage } from "./pages/settings/ProfilePage";
import { AdminAISettingsRoute } from "./auth/AdminAISettingsRoute";
import { EmissionsDashboard } from "./pages/emissions/EmissionsDashboard";
import { EmissionsReportDetail } from "./pages/emissions/EmissionsReportDetail";
import { LeakageDetectorPage } from "./pages/leakage/LeakageDetectorPage";
import { PlatformAdminRoute } from "./auth/PlatformAdminRoute";
import { PortDirectory } from "./pages/directory/PortDirectory";
import { TariffConfig } from "./pages/directory/TariffConfig";
import { TermsOfServicePage } from "./pages/TermsOfService";

function RootLayout() {
  return (
    <AuthProvider>
      <Outlet />
    </AuthProvider>
  );
}

function HydrateFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-900">
      <div className="size-8 animate-spin rounded-full border-2 border-mint-200 border-t-mint-500" />
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: "/",
    Component: RootLayout,
    errorElement: <ErrorPage />,
    hydrateFallbackElement: <HydrateFallback />,
    children: [
      {
        path: "login",
        Component: LoginPage,
      },
      {
        path: "terms-of-service",
        Component: TermsOfServicePage,
      },
      {
        Component: ProtectedRoute,
        children: [
          {
            Component: AppLayout,
            children: [
              { index: true, Component: Dashboard },
              { path: "vessels", Component: VesselList },
              { path: "vessels/new", Component: VesselForm },
              { path: "vessels/:vesselId", Component: VesselDetail },
              { path: "vessels/:vesselId/edit", Component: VesselForm },
              { path: "port-calls", Component: PortCallList },
              { path: "port-calls/new", Component: PortCallWizard },
              {
                path: "port-calls/:portCallId",
                Component: PortCallDetail,
                loader: portCallDetailLoader,
              },
              {
                path: "port-calls/:portCallId/audit",
                Component: PortCallAudit,
                loader: portCallAuditLoader,
              },
              {
                path: "port-calls/:portCallId/documents",
                Component: PortCallDocuments,
                loader: portCallDocumentsLoader,
              },
              { path: "port-calls/:portCallId/edit", Component: PortCallForm },
              { path: "da", Component: DAList },
              { path: "da/generate", Component: DAGenerate },
              { path: "da/:daId", Component: DADetail },
              { path: "emails", Component: EmailList },
              { path: "emails/:emailId", Component: EmailDetail },
              { path: "emissions", Component: EmissionsDashboard },
              { path: "emissions/reports/:id", Component: EmissionsReportDetail },
              { path: "leakage-detector", Component: LeakageDetectorPage },
              { path: "directory/ports", Component: PortDirectory },
              { path: "directory/tariffs", Component: TariffConfig },
              { path: "settings/profile", Component: ProfilePage },
              { path: "settings/integrations", Component: IntegrationsPage },
              { path: "settings/billing", Component: Billing },
              {
                path: "settings/ai",
                Component: AdminAISettingsRoute,
                children: [{ index: true, Component: AISettingsPage }],
              },
              { path: "admin/users", Component: UserList },
              { path: "admin/users/new", Component: UserForm },
              { path: "admin/users/:userId/edit", Component: UserForm },
              { path: "admin/roles", Component: RoleList },
              { path: "admin/roles/new", Component: RoleForm },
              { path: "admin/roles/:roleId/edit", Component: RoleForm },
              {
                path: "admin/companies",
                Component: PlatformAdminRoute,
                children: [
                  { index: true, Component: CompanyList },
                  { path: "new", Component: CompanyForm },
                  { path: ":companyId", Component: CompanyDetail },
                ],
              },
            ],
          },
        ],
      },
      {
        path: "*",
        Component: NotFoundPage,
      },
    ],
  },
]);
