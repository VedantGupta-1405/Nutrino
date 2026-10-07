import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { User, Save, CheckCircle2, AlertCircle, ShieldAlert } from 'lucide-react';
import { profileApi } from '../api/profile';
import { PageHeader } from '../components/common/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Select } from '../components/common/Select';
import { Textarea } from '../components/common/Textarea';
import { LoadingState } from '../components/common/LoadingState';
import { extractErrorMessage } from '../api/client';

export function ProfilePage() {
  const queryClient = useQueryClient();

  const {
    data: profile,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['profile'],
    queryFn: profileApi.getProfile,
    retry: false,
  });

  const [age, setAge] = useState('');
  const [height, setHeight] = useState('');
  const [weight, setWeight] = useState('');
  const [activityLevel, setActivityLevel] = useState('MODERATELY_ACTIVE');
  const [dietaryPreference, setDietaryPreference] = useState('VEGETARIAN');
  const [preferredCuisines, setPreferredCuisines] = useState('');
  const [allergies, setAllergies] = useState('');
  const [dislikedFoods, setDislikedFoods] = useState('');
  const [budget, setBudget] = useState('');
  const [availableIngredients, setAvailableIngredients] = useState('');

  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (profile) {
      setAge(profile.age ? String(profile.age) : '');
      setHeight(profile.height ? String(profile.height) : '');
      setWeight(profile.weight ? String(profile.weight) : '');
      setActivityLevel(profile.activity_level || 'MODERATELY_ACTIVE');
      setDietaryPreference(profile.dietary_preference || 'VEGETARIAN');
      setPreferredCuisines(profile.preferred_cuisine ? profile.preferred_cuisine.join(', ') : '');
      setAllergies(profile.allergies_or_restrictions ? profile.allergies_or_restrictions.join(', ') : '');
      setDislikedFoods(profile.disliked_foods ? profile.disliked_foods.join(', ') : '');
      setBudget(profile.budget_per_day ? String(profile.budget_per_day) : '');
      setAvailableIngredients(profile.available_ingredients ? profile.available_ingredients.join(', ') : '');
    }
  }, [profile]);

  const updateMutation = useMutation({
    mutationFn: (data) => profileApi.updateProfile(data),
    onSuccess: () => {
      setSuccessMsg('Dietary and health profile saved successfully.');
      setErrorMsg('');
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-recommendation'] });
      setTimeout(() => setSuccessMsg(''), 4000);
    },
    onError: (err) => {
      setErrorMsg(extractErrorMessage(err, 'Failed to update profile.'));
      setSuccessMsg('');
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();

    const parseList = (str) =>
      str
        ? str
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean)
        : [];

    updateMutation.mutate({
      age: age ? parseInt(age, 10) : null,
      height: height ? parseFloat(height) : null,
      weight: weight ? parseFloat(weight) : null,
      activity_level: activityLevel,
      dietary_preference: dietaryPreference,
      preferred_cuisine: parseList(preferredCuisines),
      allergies_or_restrictions: parseList(allergies),
      disliked_foods: parseList(dislikedFoods),
      budget_per_day: budget ? parseFloat(budget) : null,
      available_ingredients: parseList(availableIngredients),
    });
  };

  return (
    <div className="space-y-8 max-w-4xl">
      <PageHeader
        title="Dietary & Physical Profile"
        description="Persistent physical metrics, dietary preferences, allergen exclusions, and pantry inventory used for personalization."
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

      {isLoading ? (
        <LoadingState message="Loading profile settings..." type="skeleton" />
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Section 1: Physical Metrics */}
          <Card className="p-6 sm:p-8 border-slate-200/90">
            <CardHeader>
              <CardTitle className="text-base">Physical & Activity Baseline</CardTitle>
              <CardDescription>Metrics for basal metabolic and caloric estimations.</CardDescription>
            </CardHeader>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
              <Input
                label="Age (Years)"
                type="number"
                placeholder="28"
                value={age}
                onChange={(e) => setAge(e.target.value)}
              />
              <Input
                label="Height (cm)"
                type="number"
                step="0.1"
                placeholder="175"
                value={height}
                onChange={(e) => setHeight(e.target.value)}
              />
              <Input
                label="Weight (kg)"
                type="number"
                step="0.1"
                placeholder="70"
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
              />
            </div>

            <div className="mt-4">
              <Select
                label="Daily Physical Activity Level"
                value={activityLevel}
                onChange={(e) => setActivityLevel(e.target.value)}
                options={[
                  { value: 'SEDENTARY', label: 'Sedentary (Little or no exercise, desk work)' },
                  { value: 'LIGHTLY_ACTIVE', label: 'Lightly Active (Light exercise 1-3 days/week)' },
                  { value: 'MODERATELY_ACTIVE', label: 'Moderately Active (Moderate exercise 3-5 days/week)' },
                  { value: 'VERY_ACTIVE', label: 'Very Active (Hard exercise 6-7 days/week)' },
                  { value: 'EXTRA_ACTIVE', label: 'Extra Active (Physical labor or intense training)' },
                ]}
              />
            </div>
          </Card>

          {/* Section 2: Dietary Preferences & Allergies */}
          <Card className="p-6 sm:p-8 border-slate-200/90">
            <CardHeader>
              <CardTitle className="text-base">Dietary Patterns & Allergen Exclusions</CardTitle>
              <CardDescription>
                Strict constraints enforced by the recommendation engine. Foods matching allergies or dietary restrictions are never recommended.
              </CardDescription>
            </CardHeader>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
              <Select
                label="Dietary Pattern"
                value={dietaryPreference}
                onChange={(e) => setDietaryPreference(e.target.value)}
                options={[
                  { value: 'VEGETARIAN', label: 'Vegetarian (No meat, fish, poultry)' },
                  { value: 'VEGAN', label: 'Vegan (Strict plant-based, no dairy)' },
                  { value: 'NON_VEGETARIAN', label: 'Non-Vegetarian (All foods)' },
                  { value: 'EGGETARIAN', label: 'Eggetarian (Vegetarian + eggs)' },
                  { value: 'PESCATARIAN', label: 'Pescatarian (Vegetarian + fish)' },
                  { value: 'KETO', label: 'Ketogenic (Low carb, high fat)' },
                  { value: 'PALEO', label: 'Paleolithic' },
                  { value: 'ANY', label: 'Any / No Restriction' },
                ]}
              />

              <Input
                label="Preferred Cuisines"
                placeholder="e.g. Indian, Mediterranean, Asian"
                value={preferredCuisines}
                onChange={(e) => setPreferredCuisines(e.target.value)}
                helperText="Comma separated cuisine keywords"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
              <Input
                label="Allergies / Restrictions (Strictly Excluded)"
                placeholder="e.g. peanuts, dairy, paneer, shellfish"
                value={allergies}
                onChange={(e) => setAllergies(e.target.value)}
                helperText="Items matching these terms will be strictly rejected"
              />

              <Input
                label="Disliked Foods (Avoided)"
                placeholder="e.g. mushroom, eggplant, olives"
                value={dislikedFoods}
                onChange={(e) => setDislikedFoods(e.target.value)}
                helperText="Excluded from suggestions when alternatives exist"
              />
            </div>
          </Card>

          {/* Section 3: Kitchen Pantry & Budget */}
          <Card className="p-6 sm:p-8 border-slate-200/90">
            <CardHeader>
              <CardTitle className="text-base">Pantry Inventory & Budget</CardTitle>
              <CardDescription>Available ingredients are scored higher for meal recommendations.</CardDescription>
            </CardHeader>

            <div className="space-y-4 mt-4">
              <Input
                label="Available Kitchen Ingredients"
                placeholder="e.g. rice, toor dal, onion, tomato, spinach, curd"
                value={availableIngredients}
                onChange={(e) => setAvailableIngredients(e.target.value)}
                helperText="Comma separated list of items currently in your kitchen"
              />

              <Input
                label="Estimated Daily Budget (Currency Units)"
                type="number"
                placeholder="e.g. 300"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                helperText="Note: Food catalog does not track pricing; budget constraints are treated transparently."
              />
            </div>
          </Card>

          <div className="flex justify-end pt-2">
            <Button
              type="submit"
              variant="primary"
              size="md"
              loading={updateMutation.isPending}
              icon={Save}
            >
              Save Profile Settings
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}
