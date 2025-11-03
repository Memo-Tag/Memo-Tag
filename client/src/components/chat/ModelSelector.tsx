import { Check, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface Model {
  id: string;
  name: string;
  description: string;
  category: string;
  recommended?: boolean;
}

interface ModelSelectorProps {
  models: Model[];
  selectedModel: string;
  provider?: string;
  onSelectModel: (modelId: string) => void;
}

export function ModelSelector({
  models,
  selectedModel,
  provider = "perplexity",
  onSelectModel,
}: ModelSelectorProps) {
  const selected = models.find((m) => m.id === selectedModel);
  const providerLabel = provider?.toUpperCase() || "PERPLEXITY";

  // Group models by category
  const searchModels = models.filter((m) => m.category === "search");
  const reasoningModels = models.filter((m) => m.category === "reasoning");
  const fastModels = models.filter((m) => m.category === "fast");
  const advancedModels = models.filter((m) => m.category === "advanced");
  const premiumModels = models.filter((m) => m.category === "premium");

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="w-full sm:w-auto">
          <span className="font-medium">
            {providerLabel} / {selected?.name || "Select Model"}
          </span>
          {selected?.recommended && (
            <span className="ml-2 text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
              Recommended
            </span>
          )}
          <ChevronDown className="ml-2 w-4 h-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuLabel>{providerLabel} Models</DropdownMenuLabel>
        
        {searchModels.length > 0 && (
          <>
            <DropdownMenuLabel className="text-xs mt-2">Search Models</DropdownMenuLabel>
            {searchModels.map((model) => (
              <DropdownMenuItem
                key={model.id}
                onClick={() => onSelectModel(model.id)}
                className="cursor-pointer"
              >
                <div className="flex items-start gap-2 w-full">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{model.name}</span>
                      {model.recommended && (
                        <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                          ⭐
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {model.description}
                    </p>
                  </div>
                  {selectedModel === model.id && (
                    <Check className="w-4 h-4 text-primary flex-shrink-0 mt-1" />
                  )}
                </div>
              </DropdownMenuItem>
            ))}
          </>
        )}
        
        {fastModels.length > 0 && (
          <>
            <DropdownMenuLabel className="text-xs mt-2">Fast Models</DropdownMenuLabel>
            {fastModels.map((model) => (
              <DropdownMenuItem
                key={model.id}
                onClick={() => onSelectModel(model.id)}
                className="cursor-pointer"
              >
                <div className="flex items-start gap-2 w-full">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{model.name}</span>
                      {model.recommended && (
                        <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                          ⭐
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {model.description}
                    </p>
                  </div>
                  {selectedModel === model.id && (
                    <Check className="w-4 h-4 text-primary flex-shrink-0 mt-1" />
                  )}
                </div>
              </DropdownMenuItem>
            ))}
          </>
        )}
        
        {advancedModels.length > 0 && (
          <>
            <DropdownMenuLabel className="text-xs mt-2">Advanced Models</DropdownMenuLabel>
            {advancedModels.map((model) => (
              <DropdownMenuItem
                key={model.id}
                onClick={() => onSelectModel(model.id)}
                className="cursor-pointer"
              >
                <div className="flex items-start gap-2 w-full">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{model.name}</span>
                      {model.recommended && (
                        <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                          ⭐
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {model.description}
                    </p>
                  </div>
                  {selectedModel === model.id && (
                    <Check className="w-4 h-4 text-primary flex-shrink-0 mt-1" />
                  )}
                </div>
              </DropdownMenuItem>
            ))}
          </>
        )}
        
        {premiumModels.length > 0 && (
          <>
            <DropdownMenuLabel className="text-xs mt-2">Premium Models</DropdownMenuLabel>
            {premiumModels.map((model) => (
              <DropdownMenuItem
                key={model.id}
                onClick={() => onSelectModel(model.id)}
                className="cursor-pointer"
              >
                <div className="flex items-start gap-2 w-full">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{model.name}</span>
                      {model.recommended && (
                        <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                          ⭐
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {model.description}
                    </p>
                  </div>
                  {selectedModel === model.id && (
                    <Check className="w-4 h-4 text-primary flex-shrink-0 mt-1" />
                  )}
                </div>
              </DropdownMenuItem>
            ))}
          </>
        )}
        
        {reasoningModels.length > 0 && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuLabel className="text-xs">Reasoning Models</DropdownMenuLabel>
            {reasoningModels.map((model) => (
              <DropdownMenuItem
                key={model.id}
                onClick={() => onSelectModel(model.id)}
                className="cursor-pointer"
              >
                <div className="flex items-start gap-2 w-full">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{model.name}</span>
                      {model.recommended && (
                        <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                          ⭐
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {model.description}
                    </p>
                  </div>
                  {selectedModel === model.id && (
                    <Check className="w-4 h-4 text-primary flex-shrink-0 mt-1" />
                  )}
                </div>
              </DropdownMenuItem>
            ))}
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

