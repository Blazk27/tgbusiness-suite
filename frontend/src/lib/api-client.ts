import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const response = await axios.post(
          `${API_URL}/api/auth/refresh`,
          {},
          { withCredentials: true }
        );

        const { access_token } = response.data;
        localStorage.setItem("access_token", access_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem("access_token");
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: (email: string, password: string) =>
    apiClient.post("/auth/login", new URLSearchParams({ username: email, password }), {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    }),

  register: (data: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    organization_name: string;
  }) => apiClient.post("/auth/register", data),

  logout: () => apiClient.post("/auth/logout"),

  refresh: () => apiClient.post("/auth/refresh"),

  verifyEmail: (token: string) => apiClient.post("/auth/verify-email", { token }),

  forgotPassword: (email: string) => apiClient.post("/auth/forgot-password", { email }),

  resetPassword: (token: string, newPassword: string) =>
    apiClient.post("/auth/reset-password", { token, new_password: newPassword }),
};

// Accounts API
export const accountsApi = {
  list: () => apiClient.get("/accounts"),

  get: (id: string) => apiClient.get(`/accounts/${id}`),

  create: (data: FormData) =>
    apiClient.post("/accounts", data, {
      headers: { "Content-Type": "multipart/form-data" },
    }),

  update: (id: string, data: any) => apiClient.patch(`/accounts/${id}`, data),

  delete: (id: string) => apiClient.delete(`/accounts/${id}`),

  connect: (id: string) => apiClient.post(`/accounts/${id}/connect`),

  disconnect: (id: string) => apiClient.post(`/accounts/${id}/disconnect`),

  status: (id: string) => apiClient.get(`/accounts/${id}/status`),
};

// Tasks API
export const tasksApi = {
  list: (status?: string) =>
    apiClient.get("/tasks", { params: { status_filter: status } }),

  get: (id: string) => apiClient.get(`/tasks/${id}`),

  create: (data: any) => apiClient.post("/tasks", data),

  createBulk: (data: any) => apiClient.post("/tasks/bulk", data),

  cancel: (id: string) => apiClient.delete(`/tasks/${id}`),

  progress: (id: string) => apiClient.get(`/tasks/${id}/progress`),
};

// Proxies API
export const proxiesApi = {
  list: () => apiClient.get("/proxies"),

  get: (id: string) => apiClient.get(`/proxies/${id}`),

  create: (data: any) => apiClient.post("/proxies", data),

  update: (id: string, data: any) => apiClient.patch(`/proxies/${id}`, data),

  delete: (id: string) => apiClient.delete(`/proxies/${id}`),

  test: (id: string) => apiClient.post(`/proxies/${id}/test`),
};

// Billing API
export const billingApi = {
  getPlans: () => apiClient.get("/billing/plans"),

  getSubscription: () => apiClient.get("/billing/subscription"),

  subscribe: (planId: string, paymentMethodId: string) =>
    apiClient.post("/billing/subscribe", {
      plan_id: planId,
      payment_method_id: paymentMethodId,
    }),

  portal: () => apiClient.post("/billing/portal"),

  invoices: () => apiClient.get("/billing/invoices"),
};
