import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  UtensilsCrossed,
  Plus,
  Trash2,
  Clock,
  Calendar,
  AlertTriangle,
  Info,
  CheckCircle2,
} from 'lucide-react';
import { mealsApi } from '../api/meals';
import { PageHeader } from '../components/common/PageHeader';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { LoadingState } from '../components/common/LoadingState';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorState } from '../components/common/ErrorState';
import { LogMealModal } from '../components/meals/LogMealModal';

export function MealsPage() {
  const queryClient = useQueryClient();
  const [logMealOpen, setLogMealOpen] = useState(false);
  const [selectedMeal, setSelectedMeal] = useState(null);
  const [mealToDelete, setMealToDelete] = useState(null);

  // 1. Fetch User Meals
  const {
    data: meals,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['meals'],
    queryFn: () => mealsApi.listMeals(50, 0),
  });

  // 2. Delete Meal Mutation
  const deleteMutation = useMutation({
    mutationFn: (mealId) => mealsApi.deleteMeal(mealId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meals'] });
      queryClient.invalidateQueries({ queryKey: ['today-meals'] });
      queryClient.invalidateQueries({ queryKey: ['today-nutrition'] });
      setMealToDelete(null);
      if (selectedMeal?.id === mealToDelete?.id) {
        setSelectedMeal(null);
      }
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Meal Log & History"
        description="Review all recorded meal occasions, inspect historical nutritional snapshots, and delete logged entries."
        action={
          <Button
            variant="primary"
            size="md"
            icon={Plus}
            onClick={() => setLogMealOpen(true)}
          >
            Log Meal
          </Button>
        }
      />

      {isLoading ? (
        <LoadingState message="Loading meal records..." type="skeleton" />
      ) : error ? (
        <ErrorState
          title="Could not load meals"
          message={error.message || 'Failed to retrieve meal log from server.'}
          onRetry={refetch}
        />
      ) : !meals || meals.length === 0 ? (
        <EmptyState
          icon={UtensilsCrossed}
          title="No meals logged yet"
          description="Log your first meal using conversational natural language to start tracking your nutritional intake."
          action={
            <Button
              variant="primary"
              size="sm"
              icon={Plus}
              onClick={() => setLogMealOpen(true)}
            >
              Log First Meal
            </Button>
          }
        />
      ) : (
        <div className="space-y-3">
          {meals.map((meal) => {
            const consumedDate = new Date(meal.consumed_at);
            const dateStr = consumedDate.toLocaleDateString(undefined, {
              weekday: 'short',
              month: 'short',
              day: 'numeric',
            });
            const timeStr = consumedDate.toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            });

            return (
              <Card
                key={meal.id}
                hover
                className="p-4 sm:p-5 border-slate-200/80 transition-all flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 cursor-pointer"
                onClick={() => setSelectedMeal(meal)}
              >
                <div className="flex items-start gap-4 min-w-0">
                  <div className="p-3 bg-emerald-50 rounded-xl text-emerald-700 shrink-0 border border-emerald-100/80">
                    <UtensilsCrossed className="w-5 h-5" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant="brand" size="sm">{meal.meal_type}</Badge>
                      <span className="text-xs text-slate-500 flex items-center gap-1 font-medium">
                        <Calendar className="w-3 h-3 text-slate-400" />
                        {dateStr}
                      </span>
                      <span className="text-xs text-slate-400 flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-400" />
                        {timeStr}
                      </span>
                    </div>

                    <div className="mt-2 text-xs text-slate-700 line-clamp-1">
                      {meal.items?.map((item) => (
                        <span key={item.id} className="mr-3">
                          <strong className="text-slate-900">{item.food_name}</strong> ({Number(item.quantity)} {item.unit})
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between sm:justify-end gap-6 pt-3 sm:pt-0 border-t sm:border-t-0 border-slate-100 shrink-0">
                  <div className="text-right">
                    <div className="text-base font-bold text-slate-900">
                      {Math.round(Number(meal.total_calories || 0))} <span className="text-xs font-normal text-slate-500">kcal</span>
                    </div>
                    <div className="text-[11px] text-slate-400">
                      P: {Math.round(Number(meal.total_protein || 0))}g • C: {Math.round(Number(meal.total_carbohydrates || 0))}g • F: {Math.round(Number(meal.total_fat || 0))}g
                    </div>
                  </div>

                  <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                    <button
                      type="button"
                      onClick={() => setMealToDelete(meal)}
                      className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                      title="Delete meal record"
                      aria-label="Delete meal record"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Meal Details Modal */}
      {selectedMeal && (
        <Modal
          isOpen={!!selectedMeal}
          onClose={() => setSelectedMeal(null)}
          title={`${selectedMeal.meal_type} Details`}
          description={`Consumed at ${new Date(selectedMeal.consumed_at).toLocaleString()}`}
          maxWidth="lg"
          footer={
            <div className="flex items-center justify-between w-full">
              <Button
                variant="danger"
                size="sm"
                icon={Trash2}
                onClick={() => {
                  setMealToDelete(selectedMeal);
                }}
              >
                Delete Meal
              </Button>
              <Button variant="outline" size="sm" onClick={() => setSelectedMeal(null)}>
                Close
              </Button>
            </div>
          }
        >
          <div className="space-y-4">
            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80 grid grid-cols-4 gap-2 text-center">
              <div>
                <span className="text-[10px] font-semibold text-slate-400 uppercase">Calories</span>
                <p className="text-base font-bold text-slate-900 mt-0.5">{Math.round(Number(selectedMeal.total_calories))} kcal</p>
              </div>
              <div>
                <span className="text-[10px] font-semibold text-slate-400 uppercase">Protein</span>
                <p className="text-base font-bold text-slate-900 mt-0.5">{Math.round(Number(selectedMeal.total_protein))}g</p>
              </div>
              <div>
                <span className="text-[10px] font-semibold text-slate-400 uppercase">Carbs</span>
                <p className="text-base font-bold text-slate-900 mt-0.5">{Math.round(Number(selectedMeal.total_carbohydrates))}g</p>
              </div>
              <div>
                <span className="text-[10px] font-semibold text-slate-400 uppercase">Fat</span>
                <p className="text-base font-bold text-slate-900 mt-0.5">{Math.round(Number(selectedMeal.total_fat))}g</p>
              </div>
            </div>

            <div>
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Itemized Breakdown</h4>
              <div className="divide-y divide-slate-100 border border-slate-200/80 rounded-xl overflow-hidden bg-white">
                {selectedMeal.items?.map((item) => (
                  <div key={item.id} className="p-3 flex items-center justify-between text-xs">
                    <div>
                      <p className="font-semibold text-slate-900">{item.food_name}</p>
                      <p className="text-slate-500 text-[11px] mt-0.5">Portion: {Number(item.quantity)} {item.unit}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-slate-900">{Math.round(Number(item.calculated_calories))} kcal</p>
                      <p className="text-[11px] text-slate-400">
                        P: {Number(item.calculated_protein)}g • C: {Number(item.calculated_carbohydrates)}g • F: {Number(item.calculated_fat)}g
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* Delete Confirmation Modal */}
      {mealToDelete && (
        <Modal
          isOpen={!!mealToDelete}
          onClose={() => setMealToDelete(null)}
          title="Confirm Meal Deletion"
          description="Are you sure you want to delete this meal record? This action will permanently remove its nutritional snapshot from your daily aggregates."
          maxWidth="md"
          footer={
            <div className="flex items-center justify-end gap-3 w-full">
              <Button variant="ghost" size="sm" onClick={() => setMealToDelete(null)}>
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                icon={Trash2}
                loading={deleteMutation.isPending}
                onClick={() => deleteMutation.mutate(mealToDelete.id)}
              >
                Delete Record
              </Button>
            </div>
          }
        >
          <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-amber-800 text-xs flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-amber-600" />
            <span className="leading-relaxed">
              Deleting this <strong>{mealToDelete.meal_type}</strong> record ({Math.round(Number(mealToDelete.total_calories))} kcal) cannot be undone.
            </span>
          </div>
        </Modal>
      )}

      {/* Log Meal Natural Language Modal */}
      <LogMealModal isOpen={logMealOpen} onClose={() => setLogMealOpen(false)} />
    </div>
  );
}
