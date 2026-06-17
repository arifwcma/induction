"use client";

import { createContext, useContext } from "react";

const TrainerContext = createContext<boolean>(false);

export function TrainerProvider({
  canTrain,
  children,
}: {
  canTrain: boolean;
  children: React.ReactNode;
}) {
  return <TrainerContext.Provider value={canTrain}>{children}</TrainerContext.Provider>;
}

export function useCanTrain(): boolean {
  return useContext(TrainerContext);
}
