interface ColorPaletteProps {
  colors: string[];
}

export default function ColorPalette({ colors }: ColorPaletteProps) {
  return (
    <div className="flex gap-1">
      {colors.map((color, i) => (
        <div
          key={i}
          className="w-6 h-6 rounded"
          style={{ backgroundColor: color }}
          title={color}
        />
      ))}
    </div>
  );
}
