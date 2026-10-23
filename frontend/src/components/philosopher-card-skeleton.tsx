import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function PhilosopherCardSkeleton() {
  return (
    <Card aria-hidden="true" className="gap-0 rounded-2xl p-3 shadow-none">
      <Skeleton className="aspect-square w-full rounded-xl" />
      <CardHeader className="gap-3 px-3 pt-5">
        <Skeleton className="h-6 w-1/2" />
      </CardHeader>
      <CardContent className="flex flex-1 flex-col gap-2 px-3 pt-4">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </CardContent>
      <CardFooter className="gap-2 px-3 pt-6 pb-3">
        <Skeleton className="h-12 flex-1 rounded-xl" />
        <Skeleton className="h-12 flex-1 rounded-xl" />
      </CardFooter>
    </Card>
  );
}
