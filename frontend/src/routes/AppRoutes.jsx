import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { AppLayout } from '../layouts/AppLayout';
import { PublicLayout } from '../layouts/PublicLayout';
import { LandingPage } from '../pages/LandingPage';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';
import { DashboardPage } from '../pages/DashboardPage';
import { MealsPage } from '../pages/MealsPage';
import { NutritionPage } from '../pages/NutritionPage';
import { RecommendationsPage } from '../pages/RecommendationsPage';
import { AssistantPage } from '../pages/AssistantPage';
import { GoalsPage } from '../pages/GoalsPage';
import { ProfilePage } from '../pages/ProfilePage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { LoadingState } from '../components/common/LoadingState';

function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <LoadingState message="Verifying session..." description="Authenticating access credentials" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

function PublicAuthRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <LoadingState message="Loading..." />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

export function AppRoutes() {
  return (
    <Routes>
      {/* Public Pages */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route
          path="/login"
          element={
            <PublicAuthRoute>
              <LoginPage />
            </PublicAuthRoute>
          }
        />
        <Route
          path="/register"
          element={
            <PublicAuthRoute>
              <RegisterPage />
            </PublicAuthRoute>
          }
        />
      </Route>

      {/* Authenticated Dashboard Shell */}
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/meals" element={<MealsPage />} />
        <Route path="/nutrition" element={<NutritionPage />} />
        <Route path="/recommendations" element={<RecommendationsPage />} />
        <Route path="/assistant" element={<AssistantPage />} />
        <Route path="/goals" element={<GoalsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Route>

      {/* 404 Catch-All */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
