declare module "@/components/OptionWheel" {
  import type { ComponentType } from "react";

  type OptionWheelProps = {
    items?: string[];
    defaultSelected?: number;
    onChange?: (index: number, item: string) => void;
    textColor?: string;
    activeColor?: string;
    side?: "left" | "right";
    fontSize?: number;
    spacing?: number;
    curve?: number;
    tilt?: number;
    blur?: number;
    fade?: number;
    minOpacity?: number;
    smoothing?: number;
    inset?: number;
    loop?: boolean;
    draggable?: boolean;
    soundUrl?: string;
    soundVolume?: number;
    className?: string;
  };

  const OptionWheel: ComponentType<OptionWheelProps>;
  export default OptionWheel;
}
