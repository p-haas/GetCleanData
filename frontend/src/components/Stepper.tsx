import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Step {
  label: string;
  description: string;
}

interface StepperProps {
  steps: Step[];
  currentStep: number;
  onStepClick?: (step: number) => void;
}

export const Stepper = ({ steps, currentStep, onStepClick }: StepperProps) => {
  return (
    <nav aria-label="Progress" className="mb-8">
      <ol className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;
          const isClickable = onStepClick && index < currentStep;

          return (
            <li key={step.label} className="flex-1 relative">
              <div className="flex items-center">
                {/* Connector line */}
                {index !== 0 && (
                  <div className="flex-1 h-0.5 -ml-px">
                    <div
                      className={cn(
                        'h-full transition-colors duration-300',
                        isCompleted ? 'bg-primary' : 'bg-border'
                      )}
                    />
                  </div>
                )}

                {/* Step indicator */}
                <div className="flex flex-col items-center relative group">
                  <button
                    onClick={() => isClickable && onStepClick(index)}
                    disabled={!isClickable}
                    className={cn(
                      'w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300',
                      isCompleted && 'bg-primary text-primary-foreground',
                      isCurrent && 'bg-primary text-primary-foreground ring-4 ring-primary/20',
                      !isCompleted && !isCurrent && 'bg-muted text-muted-foreground',
                      isClickable && 'cursor-pointer hover:scale-110'
                    )}
                  >
                    {isCompleted ? (
                      <Check className="w-5 h-5" />
                    ) : (
                      <span>{index + 1}</span>
                    )}
                  </button>
                  
                  <div className="mt-2 text-center min-w-[120px]">
                    <p
                      className={cn(
                        'text-sm font-medium transition-colors',
                        isCurrent && 'text-foreground',
                        !isCurrent && 'text-muted-foreground'
                      )}
                    >
                      {step.label}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {step.description}
                    </p>
                  </div>
                </div>

                {/* Connector line */}
                {index !== steps.length - 1 && (
                  <div className="flex-1 h-0.5 -mr-px">
                    <div
                      className={cn(
                        'h-full transition-colors duration-300',
                        isCompleted ? 'bg-primary' : 'bg-border'
                      )}
                    />
                  </div>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
};
