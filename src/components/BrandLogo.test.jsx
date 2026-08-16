import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import BrandLogo from "./BrandLogo";

describe("BrandLogo", () => {
  it("exposes an accessible product identity", () => {
    render(<BrandLogo />);
    expect(screen.getByLabelText("ReWeave Circular Intelligence")).toBeInTheDocument();
    expect(screen.getByText("ReWeave")).toBeVisible();
  });
});
