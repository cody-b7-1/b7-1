import { createBrowserRouter } from "react-router";

import { AuthLayout, authLayoutLoader } from "@/layouts/auth-layout";
import { RootLayout } from "@/layouts/root-layout";
import { ChatPage } from "@/pages/chat-page";
import { HomePage } from "@/pages/home-page";
import { LoginPage } from "@/pages/login-page";
import { SignupPage } from "@/pages/signup-page";
import { VerifyEmailPage } from "@/pages/verify-email-page";

export const router = createBrowserRouter([
  {
    element: <RootLayout />,
    children: [
      { path: "/", element: <HomePage /> },
      { path: "/chat/:philosopherId", element: <ChatPage /> },
      {
        element: <AuthLayout />,
        loader: authLayoutLoader,
        children: [
          { path: "/login", element: <LoginPage /> },
          { path: "/signup", element: <SignupPage /> },
          { path: "/verify-email", element: <VerifyEmailPage /> },
        ],
      },
    ],
  },
]);
