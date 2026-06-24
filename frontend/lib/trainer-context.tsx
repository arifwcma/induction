"use client";

import { createContext, useContext } from "react";

type TrainerContextValue = {
  canTrain: boolean;
  sessionId: string;
  openAddToKb: () => void;
};

const TrainerContext = createContext<TrainerContextValue>({
  canTrain: false,
  sessionId: "",
  openAddToKb: () => {},
});

export function TrainerProvider({
  canTrain,
  sessionId,
  openAddToKb,
  children,
}: {
  canTrain: boolean;
  sessionId: string;
  openAddToKb: () => void;
  children: React.ReactNode;
}) {
  return (
    <TrainerContext.Provider value={{ canTrain, sessionId, openAddToKb }}>
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
