import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Mail, Lock, UserPlus, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Card } from '../components/common/Card';
import { extractErrorMessage } from '../api/client';

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name || !email || !password) {
      setError('Please fill in all required fields.');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    setError('');
    setLoading(true);

    try {
      await register(name.trim(), email.trim(), password);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to create account. Please check your details and try again.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="py-12 sm:py-20 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Create your account</h1>
          <p className="mt-2 text-xs text-slate-500">Start precision tracking your daily nutrition and active goals</p>
        </div>

        <Card className="p-6 sm:p-8 border-slate-200/90 shadow-lg">
          {error && (
            <div className="mb-5 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span className="leading-relaxed">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Full Name"
              type="text"
              placeholder="e.g. Alex Morgan"
              icon={User}
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              autoComplete="name"
            />

            <Input
              label="Email Address"
              type="email"
              placeholder="name@example.com"
              icon={Mail}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />

            <Input
              label="Password"
              type="password"
              placeholder="Minimum 8 characters"
              icon={Lock}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              helperText="Must be at least 8 characters long"
              required
              autoComplete="new-password"
            />

            <div className="pt-2">
              <Button
                type="submit"
                variant="primary"
                size="md"
                loading={loading}
                icon={UserPlus}
                className="w-full"
              >
                Create Account
              </Button>
            </div>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-100 text-center">
            <p className="text-xs text-slate-500">
              Already have an account?{' '}
              <Link to="/login" className="font-semibold text-emerald-600 hover:text-emerald-700">
                Sign in
              </Link>
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
