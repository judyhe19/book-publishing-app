// src/features/reports/pages/ReportsPage.jsx
import React, { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { getDefaultQuarterRange } from "../../../shared/utils/quarterUtils";
import {
  exportAllAuthorsRoyaltyReport,
  exportPublisherProfitReport,
  exportAmazonSalesReport,
} from "../api/reportApi";
import {
  PageHeader,
  Button,
  Card,
  CardContent,
  ErrorAlert,
  QuarterRangePicker,
} from "../../../shared/components";

/**
 * Reports Hub — central page for all report exports.
 * Reuses shared Card, Button, PageHeader, ErrorAlert, and QuarterRangePicker components.
 */
export default function ReportsPage() {
  const navigate = useNavigate();
  const defaults = useMemo(() => getDefaultQuarterRange(), []);

  // All Authors Royalty Report state
  const [aarStartYear, setAarStartYear] = useState(String(defaults.startYear));
  const [aarStartQ, setAarStartQ] = useState(defaults.startQ);
  const [aarEndYear, setAarEndYear] = useState(String(defaults.endYear));
  const [aarEndQ, setAarEndQ] = useState(defaults.endQ);
  const [aarLoading, setAarLoading] = useState(false);
  const [aarError, setAarError] = useState("");

  // Publisher Profit Report state
  const [ppStartYear, setPpStartYear] = useState(String(defaults.startYear));
  const [ppStartQ, setPpStartQ] = useState(defaults.startQ);
  const [ppEndYear, setPpEndYear] = useState(String(defaults.endYear));
  const [ppEndQ, setPpEndQ] = useState(defaults.endQ);
  const [ppLoading, setPpLoading] = useState(false);
  const [ppError, setPpError] = useState("");

  // Amazon Sales Report state
  const [amazonLoading, setAmazonLoading] = useState(false);
  const [amazonError, setAmazonError] = useState("");

  // --- Handlers ---

  async function handleExportAllAuthorsRoyalty() {
    setAarLoading(true);
    setAarError("");
    try {
      await exportAllAuthorsRoyaltyReport(
        Number(aarStartYear), aarStartQ,
        Number(aarEndYear), aarEndQ
      );
    } catch (err) {
      setAarError(err.message || "Failed to export report.");
    } finally {
      setAarLoading(false);
    }
  }

  async function handleExportPublisherProfit() {
    setPpLoading(true);
    setPpError("");
    try {
      await exportPublisherProfitReport(
        Number(ppStartYear), ppStartQ,
        Number(ppEndYear), ppEndQ
      );
    } catch (err) {
      setPpError(err.message || "Failed to export report.");
    } finally {
      setPpLoading(false);
    }
  }

  async function handleExportAmazonSales() {
    setAmazonLoading(true);
    setAmazonError("");
    try {
      await exportAmazonSalesReport();
    } catch (err) {
      setAmazonError(err.message || "Failed to export report.");
    } finally {
      setAmazonLoading(false);
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <PageHeader
        title="Reports"
        subtitle="Generate and export financial reports."
      />

      {/* 1. Author Royalty Report (existing per-author page) */}
      <Card className="mb-6">
        <CardContent>
          <h2 className="text-lg font-semibold text-slate-900 mb-1">
            Author Royalty Report
          </h2>
          <p className="text-sm text-slate-500 mb-4">
            View a detailed per-book royalty breakdown for a specific author. Displays in-browser with print/PDF support.
          </p>
          <Button onClick={() => navigate("/reports/royalty")}>
            Open Report →
          </Button>
        </CardContent>
      </Card>

      {/* 2. All Authors Royalty Report (XLSX export) */}
      <Card className="mb-6">
        <CardContent>
          <h2 className="text-lg font-semibold text-slate-900 mb-1">
            All Authors Royalty Report
          </h2>
          <p className="text-sm text-slate-500 mb-4">
            Export total royalties earned per author per quarter as an XLSX file.
          </p>
          <div className="flex flex-wrap gap-4 items-end">
            <QuarterRangePicker
              startYear={aarStartYear}
              onStartYearChange={setAarStartYear}
              startQuarter={aarStartQ}
              onStartQuarterChange={setAarStartQ}
              endYear={aarEndYear}
              onEndYearChange={setAarEndYear}
              endQuarter={aarEndQ}
              onEndQuarterChange={setAarEndQ}
            />
            <Button
              variant="success"
              onClick={handleExportAllAuthorsRoyalty}
              disabled={aarLoading}
            >
              {aarLoading ? "Exporting…" : "Export XLSX"}
            </Button>
          </div>
          {aarError && (
            <ErrorAlert variant="leftBorder" className="mt-4">{aarError}</ErrorAlert>
          )}
        </CardContent>
      </Card>

      {/* 3. Publisher Profit Report (XLSX export) */}
      <Card className="mb-6">
        <CardContent>
          <h2 className="text-lg font-semibold text-slate-900 mb-1">
            Publisher Profit Report
          </h2>
          <p className="text-sm text-slate-500 mb-4">
            Export publisher profit per book per quarter as an XLSX file. Profit = publisher revenue − author royalty.
          </p>
          <div className="flex flex-wrap gap-4 items-end">
            <QuarterRangePicker
              startYear={ppStartYear}
              onStartYearChange={setPpStartYear}
              startQuarter={ppStartQ}
              onStartQuarterChange={setPpStartQ}
              endYear={ppEndYear}
              onEndYearChange={setPpEndYear}
              endQuarter={ppEndQ}
              onEndQuarterChange={setPpEndQ}
            />
            <Button
              variant="success"
              onClick={handleExportPublisherProfit}
              disabled={ppLoading}
            >
              {ppLoading ? "Exporting…" : "Export XLSX"}
            </Button>
          </div>
          {ppError && (
            <ErrorAlert variant="leftBorder" className="mt-4">{ppError}</ErrorAlert>
          )}
        </CardContent>
      </Card>

      {/* 4. Amazon Sales Report (XLSX export, no date range) */}
      <Card className="mb-6">
        <CardContent>
          <h2 className="text-lg font-semibold text-slate-900 mb-1">
            Amazon Sales Report
          </h2>
          <p className="text-sm text-slate-500 mb-4">
            Export lifetime Amazon sales data (print, ebook, and KENP) per book as an XLSX file.
          </p>
          <Button
            variant="success"
            onClick={handleExportAmazonSales}
            disabled={amazonLoading}
          >
            {amazonLoading ? "Exporting…" : "Export XLSX"}
          </Button>
          {amazonError && (
            <ErrorAlert variant="leftBorder" className="mt-4">{amazonError}</ErrorAlert>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
