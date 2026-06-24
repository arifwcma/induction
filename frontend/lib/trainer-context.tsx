"use client";

import { createContext, useContext } from "react";

type TrainerContextValue = {
  canTrain: boolean;
  sessionId: string;
  refreshPending: () => void;
  openAddToKb: () => void;
};

const TrainerContext = createContext<TrainerContextValue>({
  canTrain: false,
  sessionId: "",
  refreshPending: () => {},
  openAddToKb: () => {},
});

export function TrainerProvider({
  canTrain,
  sessionId,
  refreshPending,
  openAddToKb,
  children,
}: {
  canTrain: boolean;
  sessionId: string;
  refreshPending: () => void;
  openAddToKb: () => void;
  children: React.ReactNode;
}) {
  return (
    <TrainerContext.Provider value={{ canTrain, sessionId, refreshPending, openAddToKb }}>
      {children}
    </TrainerContext.Provider>
  );
}

export function useTrainer(): TrainerContextValue {
  return useContext(TrainerContext);
}

export function useCanTrain(): boolean {
  return useContext(TrainerContext).canTrain;
}
