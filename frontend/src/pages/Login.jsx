import React from 'react';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';

export default function Login() {
  return (
    <div className="auth-page">
      <h2>Login</h2>
      <form>
        <Input label="Email" type="email" name="email" />
        <Input label="Password" type="password" name="password" />
        <Button type="submit">Sign In</Button>
      </form>
    </div>
  );
}
