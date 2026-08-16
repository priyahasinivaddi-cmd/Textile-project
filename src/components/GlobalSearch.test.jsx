import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import GlobalSearch from "./GlobalSearch";
import { globalSearch } from "../services/platformService";

vi.mock("../services/platformService", () => ({ globalSearch: vi.fn() }));
describe("GlobalSearch", () => {
  it("debounces API search and displays results", async () => {
    globalSearch.mockResolvedValue({ data: { results: [{ kind: "garment", id: "WB-1", title: "WB-1", subtitle: "Cotton · Reusable", url: "/inventory" }] } });
    render(<MemoryRouter><GlobalSearch /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText("Search garments and analyses"), { target: { value: "cotton" } });
    await waitFor(() => expect(globalSearch).toHaveBeenCalledWith("cotton"), { timeout: 1000 });
    expect(await screen.findByText("WB-1")).toBeVisible();
  });
});
