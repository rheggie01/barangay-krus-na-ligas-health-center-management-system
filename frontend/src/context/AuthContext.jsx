import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import api from "../api/axios";


const AuthContext =
  createContext(null);


export function AuthProvider({
  children,
}) {
  const [
    user,
    setUser,
  ] = useState(null);

  const [
    loading,
    setLoading,
  ] = useState(true);


  // =====================================================
  // LOAD CURRENT USER
  // =====================================================

  const loadUser = async () => {
    const token =
      localStorage.getItem(
        "access_token"
      );


    if (!token) {
      setUser(null);
      setLoading(false);

      return;
    }


    try {
      const response =
        await api.get(
          "/auth/me"
        );

      setUser(
        response.data
      );

    } catch (error) {
      console.error(
        "Unable to load current user:",
        error
      );

      localStorage.removeItem(
        "access_token"
      );

      setUser(null);

    } finally {
      setLoading(false);
    }
  };


  // =====================================================
  // LOGIN
  // =====================================================

  const login = async (
    username,
    password
  ) => {
    const response =
      await api.post(
        "/auth/login",
        {
          username,
          password,
        }
      );


    localStorage.setItem(
      "access_token",
      response.data.access_token
    );


    await loadUser();
  };


  // =====================================================
  // REGISTER
  // =====================================================

  const register = async (
    registrationData
  ) => {
    const response =
      await api.post(
        "/auth/register",
        registrationData
      );

    return response.data;
  };


  // =====================================================
  // LOGOUT
  // =====================================================

  const logout = () => {
    localStorage.removeItem(
      "access_token"
    );

    setUser(null);
  };


  // =====================================================
  // INITIAL LOAD
  // =====================================================

  useEffect(() => {
    loadUser();
  }, []);


  return (
    <AuthContext.Provider
      value={{
        user,
        loading,

        login,
        register,
        logout,

        isAuthenticated:
          Boolean(user),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}


export function useAuth() {
  return useContext(
    AuthContext
  );
}