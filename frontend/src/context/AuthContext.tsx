import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { User, LoginCredentials } from "../types";
import { authService } from "../services/api/auth";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Start as true to prevent flash
  const navigate = useNavigate();
  const location = useLocation();

  // Check auth on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = localStorage.getItem("access_token");
        const storedUser = localStorage.getItem("user");

        if (token && storedUser) {
          setUser(JSON.parse(storedUser));

          // Optionally verify token is still valid
          try {
            const profile = await authService.getProfile();
            setUser(profile);
            localStorage.setItem("user", JSON.stringify(profile));
          } catch (err) {
            // Token expired or invalid
            console.log("Token expired, clearing auth");
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            localStorage.removeItem("user");
            setUser(null);
          }
        }
      } catch (error) {
        console.error("Auth initialization error:", error);
        localStorage.clear();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      setIsLoading(true);
      try {
        const response = await authService.login(credentials);
        localStorage.setItem("access_token", response.access);
        localStorage.setItem("refresh_token", response.refresh);
        localStorage.setItem("user", JSON.stringify(response.user));
        setUser(response.user);

        // Navigate to the page they were trying to access, or dashboard
        const from = (location.state as any)?.from || "/dashboard";
        navigate(from, { replace: true });
      } catch (error) {
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    [navigate, location],
  );

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    setUser(null);
    navigate("/login", { replace: true });
  }, [navigate]);

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
