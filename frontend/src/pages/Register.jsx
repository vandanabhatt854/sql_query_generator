import React from 'react';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';

export default function Register() {
  return (
    <div className="auth-page">
      <h2>Register</h2>
      <form>
        <Input label="Name" type="text" name="name" />
        <Input label="Email" type="email" name="email" />
        <Input label="Password" type="password" name="password" />
        <Button type="submit">Create Account</Button>
      </form>
    </div>
  );
}
