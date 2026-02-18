import { Navigate, createBrowserRouter } from "react-router-dom";

import { AppLayout } from "../components/layout/AppLayout";
import { AdminGuard, AuthGuard, MutedGuard } from "./guards";
import { AchievementsPage } from "../pages/AchievementsPage";
import { ChallengesPage } from "../pages/ChallengesPage";
import { CheckinHistoryPage } from "../pages/CheckinHistoryPage";
import { CheckinPage } from "../pages/CheckinPage";
import { ForgotIdPage } from "../pages/ForgotIdPage";
import { HomePage } from "../pages/HomePage";
import { InsightsPage } from "../pages/InsightsPage";
import { LessonPlayerPage } from "../pages/LessonPlayerPage";
import { LoginPage } from "../pages/LoginPage";
import { MascotPage } from "../pages/MascotPage";
import { MissionFeedPage } from "../pages/MissionFeedPage";
import { MissionRespondPage } from "../pages/MissionRespondPage";
import { ProfilePage } from "../pages/ProfilePage";
import { RecoveryConfirmPage } from "../pages/RecoveryConfirmPage";
import { RegisterPage } from "../pages/RegisterPage";
import { ReportPage } from "../pages/ReportPage";
import { ResetPasswordPage } from "../pages/ResetPasswordPage";
import { TrailsPage } from "../pages/TrailsPage";
import { QuizPlayerPage } from "../pages/QuizPlayerPage";
import { OnboardingUserIdPage } from "../pages/OnboardingUserIdPage";
import { AdminAuditPage } from "../pages/admin/AdminAuditPage";
import { AdminContentPage } from "../pages/admin/AdminContentPage";
import { AdminDashboardPage } from "../pages/admin/AdminDashboardPage";
import { AdminMetricsPage } from "../pages/admin/AdminMetricsPage";
import { AdminModerationPage } from "../pages/admin/AdminModerationPage";

export const router = createBrowserRouter([
  { path: "/", element: <Navigate to="/home" replace /> },
  { path: "/register", element: <RegisterPage /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/recovery/forgot-id", element: <ForgotIdPage /> },
  { path: "/recovery/reset-password", element: <ResetPasswordPage /> },
  { path: "/recovery/confirm", element: <RecoveryConfirmPage /> },
  { path: "/onboarding/user-id", element: <OnboardingUserIdPage /> },
  {
    path: "/",
    element: (
      <AuthGuard>
        <AppLayout />
      </AuthGuard>
    ),
    children: [
      { path: "/home", element: <HomePage /> },
      { path: "/trails", element: <TrailsPage /> },
      { path: "/lessons/:id", element: <LessonPlayerPage /> },
      { path: "/quizzes/:id", element: <QuizPlayerPage /> },
      { path: "/challenges", element: <ChallengesPage /> },
      { path: "/checkin", element: <CheckinPage /> },
      { path: "/checkin/history", element: <CheckinHistoryPage /> },
      { path: "/insights", element: <InsightsPage /> },
      { path: "/coop", element: <MissionFeedPage /> },
      { path: "/coop/feed", element: <Navigate to="/coop" replace /> },
      {
        path: "/coop/missions/:id",
        element: (
          <MutedGuard>
            <MissionRespondPage />
          </MutedGuard>
        ),
      },
      { path: "/mascot", element: <MascotPage /> },
      { path: "/profile", element: <ProfilePage /> },
      { path: "/achievements", element: <AchievementsPage /> },
      { path: "/reports", element: <ReportPage /> },
    ],
  },
  {
    path: "/admin",
    element: (
      <AdminGuard>
        <AppLayout />
      </AdminGuard>
    ),
    children: [
      { index: true, element: <AdminDashboardPage /> },
      { path: "dashboard", element: <AdminDashboardPage /> },
      { path: "content", element: <AdminContentPage /> },
      { path: "moderation", element: <AdminModerationPage /> },
      { path: "audit", element: <AdminAuditPage /> },
      { path: "metrics", element: <AdminMetricsPage /> },
    ],
  },
]);
