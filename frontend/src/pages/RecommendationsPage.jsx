import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Compass,
  Sparkles,
  AlertCircle,
  Info,
  CheckCircle2,
  Send,
  Layers,
  Utensils,
  ChevronRight,
} from 'lucide-react';
import { recommendationsApi } from '../api/recommendations';
import { PageHeader } from '../components/common/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Select } from '../components/common/Select';
import { Badge } from '../components/common/Badge';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';
import { extractErrorMessage } from '../api/client';

export function RecommendationsPage() {
  const [mealType, setMealType] = useState('');
  const [focus, setFocus] = useState('');
  const [targetCalories, setTargetCalories] = useState('');
  const [customIngredients, setCustomIngredients] = useState('');
  const [notes, setNotes] = useState('');

  // 1. Recommendation Mutation / Request
  const [recommendation, setRecommendation] = useState(null);
  const [error, setError] = useState('');

  const recMutation = useMutation({
    mutationFn: (payload) => recommendationsApi.getMealRecommendation(payload),
    onSuccess: (data) => {
      setRecommendation(data);
      setError('');
    },
    onError: (err) => {
      setError(extractErrorMessage(err, 'Failed to generate personalized recommendation.'));
    },
  });

  // Initial load recommendation
  const { isLoading: initialLoading } = useQuery({
    queryKey: ['initial-recommendation'],
    queryFn: async () => {
      const data = await recommendationsApi.getMealRecommendation({ focus: 'balanced' });
      setRecommendation(data);
      return data;
    },
    staleTime: 5 * 60 * 1000,
  });

  const handleCustomSubmit = (e) => {
    e?.preventDefault();
    const payload = {};
    if (mealType) payload.meal_type = mealType;
    if (focus) payload.focus = focus;
    if (targetCalories) payload.target_calories = parseFloat(targetCalories);
    if (customIngredients.trim()) {
      payload.ingredients = customIngredients.split(',').map((s) => s.trim()).filter(Boolean);
    }
    if (notes.trim()) payload.notes = notes.trim();

    recMutation.mutate(payload);
  };

  const handlePreset = (presetParams) => {
    setMealType(presetParams.meal_type || '');
    setFocus(presetParams.focus || '');
    if (presetParams.target_calories) setTargetCalories(String(presetParams.target_calories));
    else setTargetCalories('');
    recMutation.mutate(presetParams);
  };

  const presetButtons = [
    { label: 'High-Protein Dinner', params: { meal_type: 'DINNER', focus: 'high_protein' } },
    { label: 'Light Lunch Option', params: { meal_type: 'LUNCH', focus: 'light' } },
    { label: 'Energizing Breakfast', params: { meal_type: 'BREAKFAST', focus: 'balanced' } },
    { label: 'Under 500 Calories', params: { target_calories: 500 } },
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Personalized Recommendations"
        description="Deterministic meal suggestions strictly filtered by your profile dietary patterns, allergen exclusions, and remaining daily calories."
      />

      {/* Preset Quick Chips */}
      <div>
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-2.5">
          Quick Suggestion Presets
        </span>
        <div className="flex flex-wrap gap-2.5">
          {presetButtons.map((btn) => (
            <button
              key={btn.label}
              type="button"
              disabled={recMutation.isPending}
              onClick={() => handlePreset(btn.params)}
              className="text-xs font-semibold px-3.5 py-2 rounded-lg bg-white border border-slate-200/90 text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-all shadow-xs flex items-center gap-1.5"
            >
              <Compass className="w-3.5 h-3.5 text-emerald-600" />
              <span>{btn.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Custom Request Form */}
        <Card className="lg:col-span-1 p-6 border-slate-200/90 h-fit">
          <CardHeader>
            <CardTitle className="text-sm">Filter & Customize Request</CardTitle>
            <CardDescription>Target specific meal occasions or calorie thresholds.</CardDescription>
          </CardHeader>

          <form onSubmit={handleCustomSubmit} className="space-y-4 mt-2">
            <Select
              label="Meal Occasion"
              value={mealType}
              onChange={(e) => setMealType(e.target.value)}
              options={[
                { value: '', label: 'Any Meal Occasion' },
                { value: 'BREAKFAST', label: 'Breakfast' },
                { value: 'LUNCH', label: 'Lunch' },
                { value: 'DINNER', label: 'Dinner' },
                { value: 'SNACK', label: 'Snack' },
              ]}
            />

            <Select
              label="Nutritional Focus"
              value={focus}
              onChange={(e) => setFocus(e.target.value)}
              options={[
                { value: '', label: 'Balanced (Standard)' },
                { value: 'high_protein', label: 'High Protein Priority' },
                { value: 'low_calorie', label: 'Low Calorie' },
                { value: 'light', label: 'Light / Digestive' },
              ]}
            />

            <Input
              label="Target Calories (kcal)"
              type="number"
              placeholder="e.g. 600"
              value={targetCalories}
              onChange={(e) => setTargetCalories(e.target.value)}
              helperText="Overrides remaining calculation for this recommendation"
            />

            <Input
              label="Additional Ingredients"
              placeholder="e.g. rice, dal, spinach"
              value={customIngredients}
              onChange={(e) => setCustomIngredients(e.target.value)}
              helperText="Comma separated items to prioritize"
            />

            <div className="pt-2">
              <Button
                type="submit"
                variant="primary"
                size="md"
                loading={recMutation.isPending}
                icon={Send}
                className="w-full"
              >
                Generate Recommendation
              </Button>
            </div>
          </form>
        </Card>

        {/* Results Showcase Area */}
        <div className="lg:col-span-2 space-y-6">
          {recMutation.isPending || (initialLoading && !recommendation) ? (
            <LoadingState
              message="Evaluating constraints & ranking candidates..."
              description="Filtering dietary violations, excluding allergens, and selecting optimal database foods."
            />
          ) : error ? (
            <ErrorState title="Recommendation error" message={error} onRetry={handleCustomSubmit} />
          ) : recommendation ? (
            <Card className="p-6 sm:p-8 border-slate-200/90 shadow-card">
              <div className="flex items-start justify-between gap-4 pb-6 border-b border-slate-100">
                <div>
                  <div className="flex items-center gap-2">
                    <Badge variant="brand" size="md">
                      {recommendation.meal_type || 'Personalized Suggestion'}
                    </Badge>
                  </div>
                  <h2 className="text-xl font-bold tracking-tight text-slate-900 mt-2">
                    {recommendation.recommendation_summary}
                  </h2>
                </div>

                <div className="text-right shrink-0">
                  <div className="text-2xl font-extrabold text-emerald-700">
                    {Math.round(Number(recommendation.total_calories || 0))} <span className="text-xs font-normal text-slate-500">kcal</span>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    P: {Math.round(Number(recommendation.total_protein || 0))}g • C: {Math.round(Number(recommendation.total_carbohydrates || 0))}g • F: {Math.round(Number(recommendation.total_fat || 0))}g
                  </div>
                </div>
              </div>

              {/* Rationale & Explanation */}
              <div className="py-5">
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                  Nutritional Rationale
                </h4>
                <p className="text-xs text-slate-700 leading-relaxed font-medium bg-slate-50 p-4 rounded-xl border border-slate-200/60">
                  {recommendation.explanation}
                </p>
              </div>

              {/* Itemized Recommended Foods */}
              <div>
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
                  Suggested Food Components
                </h4>
                <div className="divide-y divide-slate-100 border border-slate-200/80 rounded-xl overflow-hidden bg-white">
                  {recommendation.items?.map((item) => (
                    <div key={item.food_id} className="p-3.5 flex items-center justify-between text-xs hover:bg-slate-50/50 transition-colors">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-emerald-50 text-emerald-700">
                          <Utensils className="w-4 h-4" />
                        </div>
                        <div>
                          <p className="font-semibold text-slate-900">{item.food_name}</p>
                          <p className="text-slate-500 text-[11px]">
                            Portion: {Number(item.quantity)} {item.unit}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-slate-900">{Math.round(Number(item.calories))} kcal</p>
                        <p className="text-[11px] text-slate-400">
                          P: {Number(item.protein)}g • C: {Number(item.carbohydrates)}g • F: {Number(item.fat)}g
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Limitations & Transparency Notes */}
              {recommendation.limitations?.length > 0 && (
                <div className="mt-6 pt-5 border-t border-slate-100">
                  <div className="flex items-start gap-2 text-xs text-slate-500">
                    <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      {recommendation.limitations.map((lim, idx) => (
                        <p key={idx} className="text-[11px] text-slate-500 leading-relaxed">
                          {lim}
                        </p>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </Card>
          ) : (
            <EmptyState
              icon={Compass}
              title="No recommendations generated"
              description="Select a preset or customize parameters to obtain personalized meal ideas."
            />
          )}
        </div>
      </div>
    </div>
  );
}
