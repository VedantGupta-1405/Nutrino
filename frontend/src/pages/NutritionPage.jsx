import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { BarChart3, TrendingUp, PieChart as PieIcon, Activity } from 'lucide-react';
import { nutritionApi } from '../api/nutrition';
import { PageHeader } from '../components/common/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { ProgressIndicator } from '../components/common/ProgressIndicator';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';

export function NutritionPage() {
  // Compute past 7 days range in YYYY-MM-DD
  const { startDateStr, endDateStr } = useMemo(() => {
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - 6);
    return {
      startDateStr: start.toISOString().split('T')[0],
      endDateStr: end.toISOString().split('T')[0],
    };
  }, []);

  // 1. Fetch Today's Nutrition
  const {
    data: todayNutrition,
    isLoading: todayLoading,
    error: todayError,
    refetch: refetchToday,
  } = useQuery({
    queryKey: ['today-nutrition'],
    queryFn: nutritionApi.getTodayNutrition,
  });

  // 2. Fetch Historical 7-day Nutrition
  const {
    data: historyData,
    isLoading: historyLoading,
    error: historyError,
    refetch: refetchHistory,
  } = useQuery({
    queryKey: ['nutrition-history', startDateStr, endDateStr],
    queryFn: () => nutritionApi.getNutritionHistory(startDateStr, endDateStr),
  });

  // Format historical chart data
  const chartDays = useMemo(() => {
    if (!historyData?.days) return [];
    return historyData.days.map((d) => {
      const dateObj = new Date(d.date);
      const label = dateObj.toLocaleDateString(undefined, { weekday: 'short', month: 'numeric', day: 'numeric' });
      return {
        date: label,
        calories: Math.round(Number(d.consumed?.calories || 0)),
        targetCalories: Math.round(Number(d.target?.calories || 0)),
        protein: Math.round(Number(d.consumed?.protein || 0)),
        carbs: Math.round(Number(d.consumed?.carbohydrates || 0)),
        fat: Math.round(Number(d.consumed?.fat || 0)),
        meals: d.meals_count || 0,
      };
    });
  }, [historyData]);

  // Macro pie distribution for today
  const macroPieData = useMemo(() => {
    const p = Number(todayNutrition?.consumed?.protein || 0) * 4; // 4 kcal per g
    const c = Number(todayNutrition?.consumed?.carbohydrates || 0) * 4; // 4 kcal per g
    const f = Number(todayNutrition?.consumed?.fat || 0) * 9; // 9 kcal per g
    const total = p + c + f;
    if (total === 0) return [];
    return [
      { name: 'Protein (kcal)', value: p, color: '#059669' },
      { name: 'Carbs (kcal)', value: c, color: '#0284c7' },
      { name: 'Fat (kcal)', value: f, color: '#d97706' },
    ];
  }, [todayNutrition]);

  const consumed = todayNutrition?.consumed || {};
  const target = todayNutrition?.target || {};

  return (
    <div className="space-y-8">
      <PageHeader
        title="Nutrition Analytics"
        description="Comprehensive daily breakdown, target tracking, and multi-day trend visualizations."
      />

      {todayLoading ? (
        <LoadingState message="Loading nutrition analytics..." type="skeleton" />
      ) : todayError ? (
        <ErrorState
          title="Could not load nutrition metrics"
          message={todayError.message || 'Failed to communicate with nutrition service.'}
          onRetry={refetchToday}
        />
      ) : (
        <>
          {/* Today's Full Metrics Grid */}
          <div>
            <h3 className="text-base font-bold text-slate-900 mb-3 tracking-tight">Today's Intake vs Targets</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              {/* Calories */}
              <Card className="p-4 border-slate-200/90">
                <span className="text-[11px] font-semibold text-slate-500 uppercase">Energy</span>
                <div className="text-2xl font-bold text-slate-900 mt-1">
                  {Math.round(Number(consumed.calories || 0))} <span className="text-xs font-normal text-slate-500">kcal</span>
                </div>
                <div className="mt-3">
                  <ProgressIndicator
                    value={consumed.calories}
                    max={target.calories}
                    color="emerald"
                    size="sm"
                    showValues={false}
                  />
                  <div className="text-[11px] text-slate-500 mt-1 flex justify-between">
                    <span>Target: {Math.round(Number(target.calories || 0))}</span>
                    <span>{target.calories ? `${Math.round((Number(consumed.calories || 0) / Number(target.calories)) * 100)}%` : '-'}</span>
                  </div>
                </div>
              </Card>

              {/* Protein */}
              <Card className="p-4 border-slate-200/90">
                <span className="text-[11px] font-semibold text-slate-500 uppercase">Protein</span>
                <div className="text-2xl font-bold text-emerald-700 mt-1">
                  {Math.round(Number(consumed.protein || 0))} <span className="text-xs font-normal text-slate-500">g</span>
                </div>
                <div className="mt-3">
                  <ProgressIndicator
                    value={consumed.protein}
                    max={target.protein}
                    color="emerald"
                    size="sm"
                    showValues={false}
                  />
                  <div className="text-[11px] text-slate-500 mt-1 flex justify-between">
                    <span>Target: {Math.round(Number(target.protein || 0))}g</span>
                    <span>{target.protein ? `${Math.round((Number(consumed.protein || 0) / Number(target.protein)) * 100)}%` : '-'}</span>
                  </div>
                </div>
              </Card>

              {/* Carbohydrates */}
              <Card className="p-4 border-slate-200/90">
                <span className="text-[11px] font-semibold text-slate-500 uppercase">Carbohydrates</span>
                <div className="text-2xl font-bold text-sky-700 mt-1">
                  {Math.round(Number(consumed.carbohydrates || 0))} <span className="text-xs font-normal text-slate-500">g</span>
                </div>
                <div className="mt-3">
                  <ProgressIndicator
                    value={consumed.carbohydrates}
                    max={target.carbohydrates}
                    color="blue"
                    size="sm"
                    showValues={false}
                  />
                  <div className="text-[11px] text-slate-500 mt-1 flex justify-between">
                    <span>Target: {Math.round(Number(target.carbohydrates || 0))}g</span>
                    <span>{target.carbohydrates ? `${Math.round((Number(consumed.carbohydrates || 0) / Number(target.carbohydrates)) * 100)}%` : '-'}</span>
                  </div>
                </div>
              </Card>

              {/* Fat */}
              <Card className="p-4 border-slate-200/90">
                <span className="text-[11px] font-semibold text-slate-500 uppercase">Dietary Fat</span>
                <div className="text-2xl font-bold text-amber-700 mt-1">
                  {Math.round(Number(consumed.fat || 0))} <span className="text-xs font-normal text-slate-500">g</span>
                </div>
                <div className="mt-3">
                  <ProgressIndicator
                    value={consumed.fat}
                    max={target.fat}
                    color="amber"
                    size="sm"
                    showValues={false}
                  />
                  <div className="text-[11px] text-slate-500 mt-1 flex justify-between">
                    <span>Target: {Math.round(Number(target.fat || 0))}g</span>
                    <span>{target.fat ? `${Math.round((Number(consumed.fat || 0) / Number(target.fat)) * 100)}%` : '-'}</span>
                  </div>
                </div>
              </Card>

              {/* Fiber */}
              <Card className="p-4 border-slate-200/90">
                <span className="text-[11px] font-semibold text-slate-500 uppercase">Dietary Fiber</span>
                <div className="text-2xl font-bold text-indigo-700 mt-1">
                  {Math.round(Number(consumed.fiber || 0))} <span className="text-xs font-normal text-slate-500">g</span>
                </div>
                <div className="mt-3">
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="bg-indigo-600 h-full rounded-full"
                      style={{ width: `${Math.min((Number(consumed.fiber || 0) / 30) * 100, 100)}%` }}
                    />
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1 flex justify-between">
                    <span>Guideline: 30g</span>
                    <span>{Math.round((Number(consumed.fiber || 0) / 30) * 100)}%</span>
                  </div>
                </div>
              </Card>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Calories Consumed vs Target Bar Chart */}
            <Card className="lg:col-span-2 p-6 border-slate-200/90">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-emerald-600" />
                  <CardTitle>Recent 7-Day Calorie Intake</CardTitle>
                </div>
                <CardDescription>Daily aggregated calories consumed compared against active target.</CardDescription>
              </CardHeader>
              <CardContent className="h-64 mt-4">
                {historyLoading ? (
                  <LoadingState message="Loading trend history..." />
                ) : historyError ? (
                  <ErrorState title="History unavailable" onRetry={refetchHistory} />
                ) : chartDays.length === 0 ? (
                  <EmptyState title="No history found" description="Log meals to generate historical trends." />
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartDays} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#ffffff',
                          borderRadius: '8px',
                          border: '1px solid #e2e8f0',
                          fontSize: '12px',
                        }}
                      />
                      <Bar dataKey="calories" name="Consumed (kcal)" fill="#059669" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>

            {/* Macro Distribution Donut Chart */}
            <Card className="p-6 border-slate-200/90">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <PieIcon className="w-4 h-4 text-emerald-600" />
                  <CardTitle>Today's Macro Calorie Split</CardTitle>
                </div>
                <CardDescription>Caloric distribution between protein (4 kcal/g), carbs (4 kcal/g), and fat (9 kcal/g).</CardDescription>
              </CardHeader>
              <CardContent className="h-64 mt-4 flex items-center justify-center">
                {macroPieData.length === 0 ? (
                  <EmptyState title="No intake today" description="Macro split updates as meals are logged." />
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={macroPieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={55}
                        outerRadius={80}
                        paddingAngle={4}
                        dataKey="value"
                      >
                        {macroPieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(value) => `${Math.round(value)} kcal`}
                        contentStyle={{
                          backgroundColor: '#ffffff',
                          borderRadius: '8px',
                          border: '1px solid #e2e8f0',
                          fontSize: '12px',
                        }}
                      />
                      <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '11px' }} />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Protein Trend Line Chart */}
          <Card className="p-6 border-slate-200/90">
            <CardHeader>
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-600" />
                <CardTitle>Daily Protein Intake Trend (7 Days)</CardTitle>
              </div>
              <CardDescription>Track consistent daily dietary protein in grams.</CardDescription>
            </CardHeader>
            <CardContent className="h-60 mt-4">
              {chartDays.length === 0 ? (
                <EmptyState title="No protein history" description="Log meals to visualize protein intake trends." />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartDays} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        borderRadius: '8px',
                        border: '1px solid #e2e8f0',
                        fontSize: '12px',
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="protein"
                      name="Protein (g)"
                      stroke="#059669"
                      strokeWidth={2.5}
                      dot={{ r: 4, fill: '#059669' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
