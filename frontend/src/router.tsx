import { createBrowserRouter } from "react-router";

import { AuthLayout, authLayoutLoader } from "@/layouts/auth-layout";
import { RootLayout, rootLayoutLoader } from "@/layouts/root-layout";
import { ChatPage } from "@/pages/chat-page";
import { HomePage } from "@/pages/home-page";
import { LoginPage } from "@/pages/login-page";
import { NotFoundPage } from "@/pages/not-found-page";
import { SignupPage } from "@/pages/signup-page";
import { VerifyEmailPage } from "@/pages/verify-email-page";

export const router = createBrowserRouter([
  {
    element: <RootLayout />,
    loader: rootLayoutLoader,
    children: [
      { path: "/", element: <HomePage /> },
      // 새 대화 화면 (고정 경로라 /chats/:chatId보다 먼저 매칭되어 chatId가 비어 있음)
      { path: "/chats/new", element: <ChatPage /> },
      // 백엔드 명세에 맞춘 채팅방 상세 경로 (/chats/{chatId})
      { path: "/chats/:chatId", element: <ChatPage /> },
      {
        element: <AuthLayout />,
        loader: authLayoutLoader,
        children: [
          { path: "/login", element: <LoginPage /> },
          { path: "/signup", element: <SignupPage /> },
          { path: "/verify-email", element: <VerifyEmailPage /> },
        ],
      },
      // 정의되지 않은 모든 경로는 404 안내 페이지로 연결
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
