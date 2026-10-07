import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  UtensilsCrossed,
  MessageSquare,
  BarChart3,
  Compass,
  ArrowRight,
  Clock,
  ChevronRight,
  Flame,
  ShieldCheck,
  Target,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { nutritionApi } from '../api/nutrition';
import { mealsApi } from '../api/meals';
import { recommendationsApi } from '../api/recommendations';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { ProgressIndicator } from '../components/common/ProgressIndicator';
import { LoadingState } from '../components/common/LoadingState';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorState } from '../components/common/ErrorState';
import { LogMealModal } from '../components/meals/LogMealModal';

export function DashboardPage() {
  const { user } = useAuth();
  const [logMealOpen, setLogMealOpen] = useState(false);

  // 1. Fetch Today's Nutrition Overview
  const {
    data: nutrition,
    isLoading: nutritionLoading,
    error: nutritionError,
    refetch: refetchNutrition,
  } = useQuery({
    queryKey: ['today-nutrition'],
    queryFn: nutritionApi.getTodayNutrition,
  });

  // 2. Fetch Today's Meals
  const {
    data: todayMeals,
    isLoading: mealsLoading,
    error: mealsError,
  } = useQuery({
    queryKey: ['today-meals'],
    queryFn: mealsApi.getTodayMeals,
  });

  // 3. Fetch Recommendation Spotlight
  const {
    data: recommendation,
    isLoading: recLoading,
  } = useQuery({
    queryKey: ['dashboard-recommendation'],
    queryFn: () => recommendationsApi.getMealRecommendation({ focus: 'balanced' }),
    staleTime: 5 * 60 * 1000,
  });

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  const consumedCalories = Number(nutrition?.consumed?.calories || 0);
  const targetCalories = Number(nutrition?.target?.calories || 0);
  const remainingCalories = targetCalories > 0 ? Math.max(targetCalories - consumedCalories, 0) : 0;
  const caloriePercentage = targetCalories > 0 ? Math.min(Math.round((consumedCalories / targetCalories) * 100), 100) : 0;

  const consumedProtein = Number(nutrition?.consumed?.protein || 0);
  const targetProtein = Number(nutrition?.target?.protein || 0);

  const consumedCarbs = Number(nutrition?.consumed?.carbohydrates || 0);
  const targetCarbs = Number(nutrition?.target?.carbohydrates || 0);

  const consumedFat = Number(nutrition?.consumed?.fat || 0);
  const targetFat = Number(nutrition?.target?.fat || 0);

  return (
    <div className="space-y-8">
      {/* Header Greeting & Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-200/80">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            {getGreeting()}, {user?.name || 'there'}
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-500">
            Here is your deterministic nutrition overview and goal progress for today.
          </p>
        </div>
        <div className="flex items-center gap-2.5 shrink-0">
          <Button
            variant="primary"
            size="md"
            icon={UtensilsCrossed}
            onClick={() => setLogMealOpen(true)}
          >
            Log Meal
          </Button>
          <Link to="/assistant">
            <Button variant="outline" size="md" icon={MessageSquare}>
              Ask Nutrino
            </Button>
          </Link>
        </div>
      </div>

      {nutritionLoading ? (
        <LoadingState message="Loading today's nutrition overview..." type="skeleton" />
      ) : nutritionError ? (
        <ErrorState
          title="Could not load nutrition metrics"
          message={nutritionError.message || 'Failed to connect to backend service.'}
          onRetry={refetchNutrition}
        />
      ) : (
        <>
          {/* Main Calorie Progress Card + Macro Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Primary Calorie Card */}
            <Card className="lg:col-span-1 p-6 border-slate-200/90 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Energy Intake
                  </span>
                  <Badge variant={caloriePercentage >= 100 ? 'warning' : 'brand'}>
                    {caloriePercentage}% Goal
                  </Badge>
                </div>

                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-extrabold text-slate-900 tracking-tight">
                    {Math.round(consumedCalories)}
                  </span>
                  <span className="text-sm font-medium text-slate-500">
                    / {targetCalories > 0 ? `${Math.round(targetCalories)} kcal` : 'No target'}
                  </span>
                </div>

                <p className="text-xs text-slate-500 mt-2">
                  {targetCalories > 0 ? (
                    remainingCalories > 0 ? (
                      <span><strong>{Math.round(remainingCalories)} kcal</strong> remaining for today</span>
                    ) : (
                      <span className="text-amber-600 font-medium">Daily calorie target reached or exceeded</span>
                    )
                  ) : (
                    <span>Set a goal to view remaining allowances</span>
                  )}
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-100">
                <ProgressIndicator
                  value={consumedCalories}
                  max={targetCalories || 2000}
                  color="emerald"
                  size="lg"
                  showValues={false}
                />
              </div>
            </Card>

            {/* Macronutrient Cards */}
            <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Protein */}
              <Card className="p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-500 uppercase">Protein</span>
                    <span className="text-xs font-bold text-emerald-700">
                      {targetProtein > 0 ? `${Math.round((consumedProtein / targetProtein) * 100)}%` : '-'}
                    </span>
                  </div>
                  <div className="text-2xl font-bold text-slate-900">
                    {Math.round(consumedProtein)}g
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    Target: {targetProtein > 0 ? `${Math.round(targetProtein)}g` : 'Not set'}
                  </div>
                </div>
                <div className="mt-4">
                  <ProgressIndicator
                    value={consumedProtein}
                    max={targetProtein}
                    color="emerald"
                    size="sm"
                    showValues={false}
                  />
                </div>
              </Card>

              {/* Carbohydrates */}
              <Card className="p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-500 uppercase">Carbohydrates</span>
                    <span className="text-xs font-bold text-sky-700">
                      {targetCarbs > 0 ? `${Math.round((consumedCarbs / targetCarbs) * 100)}%` : '-'}
                    </span>
                  </div>
                  <div className="text-2xl font-bold text-slate-900">
                    {Math.round(consumedCarbs)}g
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    Target: {targetCarbs > 0 ? `${Math.round(targetCarbs)}g` : 'Not set'}
                  </div>
                </div>
                <div className="mt-4">
                  <ProgressIndicator
                    value={consumedCarbs}
                    max={targetCarbs}
                    color="blue"
                    size="sm"
                    showValues={false}
                  />
                </div>
              </Card>

              {/* Fat */}
              <Card className="p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-500 uppercase">Dietary Fat</span>
                    <span className="text-xs font-bold text-amber-700">
                      {targetFat > 0 ? `${Math.round((consumedFat / targetFat) * 100)}%` : '-'}
                    </span>
                  </div>
                  <div className="text-2xl font-bold text-slate-900">
                    {Math.round(consumedFat)}g
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    Target: {targetFat > 0 ? `${Math.round(targetFat)}g` : 'Not set'}
                  </div>
                </div>
                <div className="mt-4">
                  <ProgressIndicator
                    value={consumedFat}
                    max={targetFat}
                    color="amber"
                    size="sm"
                    showValues={false}
                  />
                </div>
              </Card>
            </div>
          </div>

          {/* Recommendation Spotlight Banner */}
          {recommendation && (
            <Card className="border-emerald-200/80 bg-gradient-to-r from-emerald-50/60 via-white to-slate-50/40 p-6">
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div className="flex items-start gap-3.5 max-w-3xl">
                  <div className="p-2.5 rounded-xl bg-emerald-600 text-white shrink-0 shadow-xs">
                    <Compass className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider">
                        Personalized Meal Recommendation
                      </span>
                      {recommendation.meal_type && (
                        <Badge variant="brand" size="sm">{recommendation.meal_type}</Badge>
                      )}
                    </div>
                    <h4 className="text-sm font-bold text-slate-900 mt-1">
                      {recommendation.recommendation_summary}
                    </h4>
                    <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                      {recommendation.explanation}
                    </p>
                  </div>
                </div>
                <Link to="/recommendations" className="shrink-0">
                  <Button variant="outline" size="sm" icon={ArrowRight}>
                    View Recommendations
                  </Button>
                </Link>
              </div>
            </Card>
          )}

          {/* Today's Meals Section */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 tracking-tight">Today's Meals</h3>
                <p className="text-xs text-slate-500">Meals logged for the current calendar date</p>
              </div>
              <Link to="/meals" className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 flex items-center gap-1">
                <span>View Full History</span>
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>

            {mealsLoading ? (
              <LoadingState message="Loading today's meals..." />
            ) : !todayMeals || todayMeals.length === 0 ? (
              <EmptyState
                icon={UtensilsCrossed}
                title="No meals logged today"
                description="Log your first meal to track intake and update remaining macro allowances."
                action={
                  <Button
                    variant="primary"
                    size="sm"
                    icon={UtensilsCrossed}
                    onClick={() => setLogMealOpen(true)}
                  >
                    Log a Meal Now
                  </Button>
                }
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {todayMeals.map((meal) => {
                  const timeStr = new Date(meal.consumed_at).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  });
                  return (
                    <Card key={meal.id} hover className="p-5 border-slate-200/80 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <Badge variant="brand" size="sm">{meal.meal_type}</Badge>
                          <span className="text-[11px] text-slate-400 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {timeStr}
                          </span>
                        </div>

                        <div className="space-y-1.5 my-3">
                          {meal.items?.map((item) => (
                            <div key={item.id} className="text-xs text-slate-700 flex justify-between">
                              <span className="font-medium text-slate-800">{item.food_name}</span>
                              <span className="text-slate-500">
                                {Number(item.quantity)} {item.unit}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                        <span className="font-bold text-slate-900">
                          {Math.round(Number(meal.total_calories || 0))} kcal
                        </span>
                        <span className="text-[11px] text-slate-500">
                          P: {Math.round(Number(meal.total_protein || 0))}g • C: {Math.round(Number(meal.total_carbohydrates || 0))}g • F: {Math.round(Number(meal.total_fat || 0))}g
                        </span>
                      </div>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>
        </>
      )}

      {/* Log Meal Natural Language Modal */}
      <LogMealModal isOpen={logMealOpen} onClose={() => setLogMealOpen(false)} />
    </div>
  );
}
