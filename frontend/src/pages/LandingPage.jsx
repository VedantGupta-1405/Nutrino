import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  ArrowRight,
  BarChart3,
  UtensilsCrossed,
  Compass,
  Target,
  CheckCircle2,
} from 'lucide-react';
import { Button } from '../components/common/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/common/Card';
import { Badge } from '../components/common/Badge';

export function LandingPage() {
  const features = [
    {
      title: 'Deterministic Nutrition Tracking',
      description: 'Zero LLM calculation errors. All calories and macronutrients are aggregated through authoritative database values and Decimal precision.',
      icon: BarChart3,
    },
    {
      title: 'Natural-Language Meal Logging',
      description: 'Log entire meals simply by describing what you ate. The AI agent resolves catalog foods and portion sizes deterministically.',
      icon: UtensilsCrossed,
    },
    {
      title: 'Personalized Meal Recommendations',
      description: 'Receive meal suggestions filtered by your dietary preferences, allergies, disliked foods, available pantry items, and remaining calorie allowance.',
      icon: Compass,
    },
    {
      title: 'Active Goal Alignment',
      description: 'Define daily targets for weight management, muscle gain, or general health. Monitor real-time calorie and macronutrient deltas.',
      icon: Target,
    },
  ];

  return (
    <div className="py-12 sm:py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Hero Section */}
        <div className="text-center max-w-3xl mx-auto">
          <Badge variant="brand" size="md" icon={ShieldCheck} className="mb-4">
            PRECISION NUTRITION PLATFORM
          </Badge>

          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-900 leading-[1.15]">
            Personalized nutrition tracking and meal guidance.
          </h1>

          <p className="mt-5 text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl mx-auto">
            Nutrino combines deterministic macronutrient computation with grounded local AI to help you log meals, understand dietary intake, monitor active goals, and receive personalized recommendations.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link to="/register">
              <Button size="lg" icon={ArrowRight} className="w-full sm:w-auto">
                Get Started
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="outline" size="lg" className="w-full sm:w-auto">
                Sign In to Account
              </Button>
            </Link>
          </div>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-500 font-medium">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Grounded Database Truth
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Strict Allergy Enforcement
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Private Local AI Agent
            </span>
          </div>
        </div>

        {/* Product Preview Card */}
        <div className="mt-16 max-w-4xl mx-auto">
          <Card className="border-slate-200/90 shadow-xl overflow-hidden bg-gradient-to-b from-white to-slate-50/50 p-6 sm:p-8">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-6 border-b border-slate-100 gap-4">
              <div>
                <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">Live System Preview</span>
                <h3 className="text-lg font-bold text-slate-900 mt-0.5">Today's Nutrition Summary</h3>
              </div>
              <Badge variant="brand">Goal: Weight Management</Badge>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
              <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs">
                <span className="text-xs text-slate-500 font-medium">Calories</span>
                <div className="text-2xl font-extrabold text-slate-900 mt-1">1,620</div>
                <div className="text-[11px] text-slate-500 mt-1">Target: 2,000 kcal (81%)</div>
              </div>
              <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs">
                <span className="text-xs text-slate-500 font-medium">Protein</span>
                <div className="text-2xl font-extrabold text-slate-900 mt-1">88g</div>
                <div className="text-[11px] text-slate-500 mt-1">Target: 110g (80%)</div>
              </div>
              <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs">
                <span className="text-xs text-slate-500 font-medium">Carbohydrates</span>
                <div className="text-2xl font-extrabold text-slate-900 mt-1">210g</div>
                <div className="text-[11px] text-slate-500 mt-1">Target: 240g (87%)</div>
              </div>
              <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs">
                <span className="text-xs text-slate-500 font-medium">Fat</span>
                <div className="text-2xl font-extrabold text-slate-900 mt-1">48g</div>
                <div className="text-[11px] text-slate-500 mt-1">Target: 60g (80%)</div>
              </div>
            </div>

            <div className="mt-6 p-4 rounded-xl bg-emerald-50/70 border border-emerald-100 flex items-start gap-3">
              <div className="p-2 bg-emerald-600 text-white rounded-lg shrink-0 mt-0.5">
                <Compass className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-emerald-900 uppercase tracking-wide">Personalized Dinner Recommendation</h4>
                <p className="text-xs text-emerald-800 mt-1 leading-relaxed">
                  Based on your remaining 380 calories and 22g protein target, a dinner of Cooked Toor Dal with a small serving of Steamed Rice fits your vegetarian profile and keeps you right on goal.
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Feature Grid */}
        <div className="mt-24">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
              Built on deterministic accuracy, not guesswork.
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              Health decisions require factual calculations. Nutrino combines verified food nutrition data with intelligent reasoning.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map((feat) => {
              const Icon = feat.icon;
              return (
                <Card key={feat.title} className="p-6 border-slate-200/80 hover:border-slate-300 transition-colors">
                  <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200/60 flex items-center justify-center text-emerald-700 mb-4">
                    <Icon className="w-5 h-5" />
                  </div>
                  <CardTitle className="text-base">{feat.title}</CardTitle>
                  <CardContent className="p-0 mt-2">
                    <p className="text-xs text-slate-600 leading-relaxed">{feat.description}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
