import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { AppLayout } from '../layouts/AppLayout';
import { DashboardPage } from '../pages/DashboardPage';
import { MealsPage } from '../pages/MealsPage';
import { NutritionPage } from '../pages/NutritionPage';
import { RecommendationsPage } from '../pages/RecommendationsPage';
import { AssistantPage } from '../pages/AssistantPage';
import { GoalsPage } from '../pages/GoalsPage';
import { ProfilePage } from '../pages/ProfilePage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { LoadingState } from '../components/common/LoadingState';

export function AppRoutes() {
  const { isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <LoadingState message="Loading Nutrino..." description="Initializing personal health workspace" />
      </div>
    );
  }

  return (
    <Routes>
      {/* Personal Single-User Application Shell */}
      <Route element={<AppLayout />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
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
