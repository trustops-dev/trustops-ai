import { render, screen, within } from "@testing-library/react";
import { expect, test } from "vitest";
import HomePage from "../../../apps/dashboard/src/app/page";

test("renders the dashboard entry point with an empty application state", () => {
  render(<HomePage />);

  const main = within(screen.getByRole("main"));
  expect(main.getByRole("heading", { level: 1, name: "TrustOps AI" })).toBeVisible();
  expect(main.getByText("No applications connected yet.")).toBeVisible();
});
