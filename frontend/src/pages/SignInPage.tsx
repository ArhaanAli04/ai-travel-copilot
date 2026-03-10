import { SignIn } from '@clerk/react';
import { useLocation } from 'react-router-dom';

const SignInPage = () => {
  const location = useLocation();
  const returnTo = location.state?.returnTo || '/planner';

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full blur-3xl"
          style={{ background: 'radial-gradient(circle, rgba(56,189,248,0.12) 0%, transparent 70%)' }} />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full blur-3xl"
          style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.12) 0%, transparent 70%)' }} />
      </div>
      <div className="relative z-10">
        <SignIn
          routing="path"
          path="/sign-in"
          fallbackRedirectUrl={returnTo}
          signUpUrl="/sign-up"
        />
      </div>
    </div>
  );
};

export default SignInPage;
