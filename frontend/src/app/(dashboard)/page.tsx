"use client";

import { useQuery } from "@tanstack/react-query";
import { accountsApi, tasksApi } from "@/lib/api-client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Smartphone, CheckCircle, XCircle, Workflow, TrendingUp } from "lucide-react";

export default function DashboardPage() {
  const { data: accounts, isLoading: accountsLoading } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => accountsApi.list().then((res) => res.data),
  });

  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ["tasks"],
    queryFn: () => tasksApi.list().then((res) => res.data),
  });

  const activeAccounts = accounts?.filter((a: any) => a.status === "active")?.length || 0;
  const failedAccounts = accounts?.filter((a: any) => a.status === "connection_error" || a.status === "banned")?.length || 0;
  const runningTasks = tasks?.filter((t: any) => t.status === "running")?.length || 0;
  const completedTasks = tasks?.filter((t: any) => t.status === "completed")?.length || 0;

  const stats = [
    {
      title: "Total Accounts",
      value: accounts?.length || 0,
      icon: Smartphone,
      color: "text-blue-500",
    },
    {
      title: "Active Accounts",
      value: activeAccounts,
      icon: CheckCircle,
      color: "text-green-500",
    },
    {
      title: "Failed Accounts",
      value: failedAccounts,
      icon: XCircle,
      color: "text-red-500",
    },
    {
      title: "Running Tasks",
      value: runningTasks,
      icon: Workflow,
      color: "text-yellow-500",
    },
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Welcome back! Here's your overview.</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add Account
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <stat.icon className={cn("h-4 w-4", stat.color)} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button variant="outline" className="w-full justify-start">
              <Plus className="mr-2 h-4 w-4" />
              Add New Account
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <Workflow className="mr-2 h-4 w-4" />
              Create Automation Task
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <TrendingUp className="mr-2 h-4 w-4" />
              Check Account Health
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Tasks</CardTitle>
            <CardDescription>Your latest automation tasks</CardDescription>
          </CardHeader>
          <CardContent>
            {tasksLoading ? (
              <div className="text-sm text-muted-foreground">Loading...</div>
            ) : tasks?.length > 0 ? (
              <div className="space-y-2">
                {tasks.slice(0, 3).map((task: any) => (
                  <div
                    key={task.id}
                    className="flex items-center justify-between text-sm"
                  >
                    <span className="font-medium">{task.type}</span>
                    <span
                      className={cn(
                        "px-2 py-1 rounded-full text-xs",
                        task.status === "completed" && "bg-green-500/20 text-green-500",
                        task.status === "running" && "bg-blue-500/20 text-blue-500",
                        task.status === "failed" && "bg-red-500/20 text-red-500",
                        task.status === "pending" && "bg-yellow-500/20 text-yellow-500"
                      )}
                    >
                      {task.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">No tasks yet</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Account Status</CardTitle>
            <CardDescription>Overview of your accounts</CardDescription>
          </CardHeader>
          <CardContent>
            {accountsLoading ? (
              <div className="text-sm text-muted-foreground">Loading...</div>
            ) : accounts?.length > 0 ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Active</span>
                  <span className="font-medium">{activeAccounts}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Inactive</span>
                  <span className="font-medium">
                    {accounts.length - activeAccounts - failedAccounts}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Failed</span>
                  <span className="font-medium text-red-500">{failedAccounts}</span>
                </div>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">No accounts yet</div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function cn(...classes: (string | undefined | null | false)[]) {
  return classes.filter(Boolean).join(" ");
}
