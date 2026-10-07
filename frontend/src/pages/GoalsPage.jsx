import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Target, Save, CheckCircle2, AlertCircle, ArrowUpRight } from 'lucide-react';
import { goalsApi } from '../api/goals';
import { nutritionApi } from '../api/nutrition';
import { PageHeader } from '../components/common/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Select } from '../components/common/Select';
import { Badge } from '../components/common/Badge';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { extractErrorMessage } from '../api/client';

export function GoalsPage() {
  const queryClient = useQueryClient();

  // 1. Fetch Active Goal
  const {
    data: goal,
    isLoading: goalLoading,
    error: goalError,
    refetch: refetchGoal,
  } = useQuery({
    queryKey: ['goal'],
    queryFn: goalsApi.getGoal,
    retry: false,
  });

  // 2. Fetch Today's Nutrition to show alignment
  const { data: todayNutrition } = useQuery({
    queryKey: ['today-nutrition'],
    queryFn: nutritionApi.getTodayNutrition,
  });

  const [goalType, setGoalType] = useState('WEIGHT_MANAGEMENT');
  const [targetCalories, setTargetCalories] = useState('2000');
  const [targetProtein, setTargetProtein] = useState('110');
  const [targetCarbs, setTargetCarbs] = useState('240');
  const [targetFat, setTargetFat] = useState('65');
  const [notes, setNotes] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (goal) {
      setGoalType(goal.goal_type || 'WEIGHT_MANAGEMENT');
      setTargetCalories(goal.target_calories ? String(Math.round(goal.target_calories)) : '');
      setTargetProtein(goal.target_protein ? String(Math.round(goal.target_protein)) : '');
      setTargetCarbs(goal.target_carbohydrates ? String(Math.round(goal.target_carbohydrates)) : '');
      setTargetFat(goal.target_fat ? String(Math.round(goal.target_fat)) : '');
      setNotes(goal.notes || '');
    }
  }, [goal]);

  const updateMutation = useMutation({
    mutationFn: (data) => goalsApi.updateGoal(data),
    onSuccess: () => {
      setSuccessMsg('Nutrition goal updated successfully.');
      setErrorMsg('');
      queryClient.invalidateQueries({ queryKey: ['goal'] });
      queryClient.invalidateQueries({ queryKey: ['today-nutrition'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-recommendation'] });
      setTimeout(() => setSuccessMsg(''), 4000);
    },
    onError: (err) => {
      setErrorMsg(extractErrorMessage(err, 'Failed to update goal.'));
      setSuccessMsg('');
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    updateMutation.mutate({
      goal_type: goalType,
      target_calories: targetCalories ? parseFloat(targetCalories) : null,
      target_protein: targetProtein ? parseFloat(targetProtein) : null,
      target_carbohydrates: targetCarbs ? parseFloat(targetCarbs) : null,
      target_fat: targetFat ? parseFloat(targetFat) : null,
      is_active: true,
      notes: notes.trim() || null,
    });
  };

  const consumed = todayNutrition?.consumed || {};

  return (
    <div className="space-y-8">
      <PageHeader
        title="Nutrition Objectives & Goals"
        description="Configure your daily energy targets and macronutrient distributions for personalized planning."
      />

      {successMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2.5 font-medium">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2.5 font-medium">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {goalLoading ? (
        <LoadingState message="Loading goal configuration..." type="skeleton" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Goal Form */}
          <Card className="lg:col-span-2 p-6 sm:p-8 border-slate-200/90">
            <CardHeader>
              <CardTitle className="text-base">Active Goal Settings</CardTitle>
              <CardDescription>
                Define your primary objective and daily target thresholds in kilocalories and grams.
              </CardDescription>
            </CardHeader>

            <form onSubmit={handleSubmit} className="space-y-5 mt-4">
              <Select
                label="Primary Objective"
                value={goalType}
                onChange={(e) => setGoalType(e.target.value)}
                options={[
                  { value: 'WEIGHT_MANAGEMENT', label: 'Weight Management (Balanced)' },
                  { value: 'MUSCLE_GAIN', label: 'Muscle Gain (Hypertrophy / High Protein)' },
                  { value: 'GENERAL_HEALTH', label: 'General Health & Vitality' },
                ]}
                required
              />

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Target Calories (kcal)"
                  type="number"
                  placeholder="2000"
                  value={targetCalories}
                  onChange={(e) => setTargetCalories(e.target.value)}
                  helperText="Recommended standard: 1800 - 2500 kcal"
                  required
                />

                <Input
                  label="Target Protein (g)"
                  type="number"
                  placeholder="110"
                  value={targetProtein}
                  onChange={(e) => setTargetProtein(e.target.value)}
                  helperText="4 kcal per gram"
                  required
                />

                <Input
                  label="Target Carbohydrates (g)"
                  type="number"
                  placeholder="240"
                  value={targetCarbs}
                  onChange={(e) => setTargetCarbs(e.target.value)}
                  helperText="4 kcal per gram"
                  required
                />

                <Input
                  label="Target Fat (g)"
                  type="number"
                  placeholder="65"
                  value={targetFat}
                  onChange={(e) => setTargetFat(e.target.value)}
                  helperText="9 kcal per gram"
                  required
                />
              </div>

              <Input
                label="Contextual Notes"
                placeholder="e.g. Training 4 days a week, preparing for 10k run"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                helperText="Optional context provided to the recommendation engine"
              />

              <div className="pt-2">
                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  loading={updateMutation.isPending}
                  icon={Save}
                >
                  Save Active Goal
                </Button>
              </div>
            </form>
          </Card>

          {/* Today's Target vs Consumed Card */}
          <div className="space-y-4">
            <Card className="p-6 border-slate-200/90">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm">Today's Alignment</CardTitle>
                  <Badge variant="brand" size="sm">Live</Badge>
                </div>
                <CardDescription>Progress towards active daily targets.</CardDescription>
              </CardHeader>

              <div className="space-y-4 mt-3">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                    <span>Energy</span>
                    <span>{Math.round(Number(consumed.calories || 0))} / {targetCalories || 0} kcal</span>
                  </div>
                  <div className="h-1.5 bg-slate-200 rounded-full mt-2 overflow-hidden">
                    <div
                      className="bg-emerald-600 h-full rounded-full"
                      style={{
                        width: `${Math.min((Number(consumed.calories || 0) / (parseFloat(targetCalories) || 1)) * 100, 100)}%`,
                      }}
                    />
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                    <span>Protein</span>
                    <span>{Math.round(Number(consumed.protein || 0))} / {targetProtein || 0} g</span>
                  </div>
                  <div className="h-1.5 bg-slate-200 rounded-full mt-2 overflow-hidden">
                    <div
                      className="bg-emerald-600 h-full rounded-full"
                      style={{
                        width: `${Math.min((Number(consumed.protein || 0) / (parseFloat(targetProtein) || 1)) * 100, 100)}%`,
                      }}
                    />
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                    <span>Carbs</span>
                    <span>{Math.round(Number(consumed.carbohydrates || 0))} / {targetCarbs || 0} g</span>
                  </div>
                  <div className="h-1.5 bg-slate-200 rounded-full mt-2 overflow-hidden">
                    <div
                      className="bg-sky-600 h-full rounded-full"
                      style={{
                        width: `${Math.min((Number(consumed.carbohydrates || 0) / (parseFloat(targetCarbs) || 1)) * 100, 100)}%`,
                      }}
                    />
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                    <span>Fat</span>
                    <span>{Math.round(Number(consumed.fat || 0))} / {targetFat || 0} g</span>
                  </div>
                  <div className="h-1.5 bg-slate-200 rounded-full mt-2 overflow-hidden">
                    <div
                      className="bg-amber-600 h-full rounded-full"
                      style={{
                        width: `${Math.min((Number(consumed.fat || 0) / (parseFloat(targetFat) || 1)) * 100, 100)}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
