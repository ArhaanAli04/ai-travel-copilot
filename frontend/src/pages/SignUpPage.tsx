import { SignUp } from '@clerk/react';

const SignUpPage = () => (
  <div className="min-h-screen flex items-center justify-center p-4">
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full blur-3xl"
        style={{ background: 'radial-gradient(circle, rgba(56,189,248,0.12) 0%, transparent 70%)' }} />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full blur-3xl"
        style={{ background: 'radial-gradient(circle, rgba(249,115,22,0.08) 0%, transparent 70%)' }} />
    </div>
    <div className="relative z-10">
      <SignUp routing="path" path="/sign-up" fallbackRedirectUrl="/planner" signInUrl="/sign-in" />
    </div>
  </div>
);

export default SignUpPage;
