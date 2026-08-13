import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { getErrorMessage } from "api/client";
import { Button } from "components/Button";
import { ErrorDisplay } from "components/ErrorDisplay";
import { LoadingIndicator } from "components/LoadingIndicator";
import { StatusBadge } from "components/StatusBadge";
import {
  getSupportCase,
  listSupportAgents,
  resolveSupportCase,
  updateSupportCase
} from "services/supportCaseService";
import type { SupportCaseStatus, UpdateSupportCasePayload } from "types/models";
import { formatDateTime, formatStatusLabel } from "utils/app";

export function SupportCaseDetailsPage() {
  const { caseId = "" } = useParams();
  const queryClient = useQueryClient();
  const [assignedAgentUserId, setAssignedAgentUserId] = useState("");
  const [priority, setPriority] = useState("MEDIUM");
  const [status, setStatus] = useState<Exclude<SupportCaseStatus, "RESOLVED">>("OPEN");
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [error, setError] = useState("");

  const caseQuery = useQuery({
    queryKey: ["support-case", caseId],
    queryFn: () => getSupportCase(caseId),
    enabled: Boolean(caseId)
  });

  const agentsQuery = useQuery({
    queryKey: ["support-agents"],
    queryFn: listSupportAgents
  });

  useEffect(() => {
    if (!caseQuery.data) {
      return;
    }

    setAssignedAgentUserId(caseQuery.data.assigned_agent_user_id ?? "");
    setPriority(caseQuery.data.priority);
    setStatus(caseQuery.data.status === "RESOLVED" ? "OPEN" : caseQuery.data.status);
    setResolutionNotes(caseQuery.data.resolution_notes ?? "");
  }, [caseQuery.data]);

  const updateMutation = useMutation({
    mutationFn: (payload: UpdateSupportCasePayload) => updateSupportCase(caseId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["support-cases"] });
      queryClient.invalidateQueries({ queryKey: ["support-case", caseId] });
      queryClient.invalidateQueries({ queryKey: ["support-investigation", caseId] });
    }
  });

  const resolveMutation = useMutation({
    mutationFn: (notes: string) => resolveSupportCase(caseId, { resolution_notes: notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["support-cases"] });
      queryClient.invalidateQueries({ queryKey: ["support-case", caseId] });
      queryClient.invalidateQueries({ queryKey: ["support-investigation", caseId] });
    }
  });

  if (caseQuery.isLoading || agentsQuery.isLoading) {
    return <LoadingIndicator label="Loading support case..." />;
  }

  if (caseQuery.isError || !caseQuery.data) {
    return <ErrorDisplay message="Unable to load support case details." onAction={() => caseQuery.refetch()} />;
  }

  if (agentsQuery.isError) {
    return <ErrorDisplay message="Unable to load support agent list." onAction={() => agentsQuery.refetch()} />;
  }

  const supportCase = caseQuery.data;

  function handleSave() {
    setError("");
    updateMutation.mutate(
      {
        assigned_agent_user_id: assignedAgentUserId || null,
        priority: priority as UpdateSupportCasePayload["priority"],
        ...(supportCase.status === "RESOLVED" ? {} : { status }),
        resolution_notes: resolutionNotes || null
      },
      {
        onError: (mutationError) => setError(getErrorMessage(mutationError))
      }
    );
  }

  function handleResolve() {
    if (!resolutionNotes.trim()) {
      setError("Resolution notes are required before resolving a case.");
      return;
    }

    setError("");
    resolveMutation.mutate(resolutionNotes.trim(), {
      onError: (mutationError) => setError(getErrorMessage(mutationError))
    });
  }

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Case details</p>
          <h1>{supportCase.issue_summary}</h1>
          <p className="inline-muted">Case ID {supportCase.id}</p>
        </div>
        <StatusBadge status={supportCase.status} />
      </div>

      <div className="content-grid">
        <article className="panel">
          <h2>Case information</h2>
          <div className="ride-summary">
            <div className="ride-summary__row">
              <span>Priority</span>
              <strong>{formatStatusLabel(supportCase.priority)}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Created by</span>
              <strong>{supportCase.created_by_user.email}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Created</span>
              <strong>{formatDateTime(supportCase.created_at)}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Resolved</span>
              <strong>{formatDateTime(supportCase.resolved_at)}</strong>
            </div>
          </div>
          <div className="panel__actions">
            <Link className="button button--ghost" to={`/support/investigations/${supportCase.id}`}>
              Open ride investigation
            </Link>
          </div>
        </article>

        <article className="panel">
          <h2>Case management</h2>
          <div className="field">
            <span className="field__label">Assigned agent</span>
            <select className="input" onChange={(event) => setAssignedAgentUserId(event.target.value)} value={assignedAgentUserId}>
              <option value="">Unassigned</option>
              {(agentsQuery.data ?? []).map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.first_name} {agent.last_name} ({agent.role})
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <span className="field__label">Priority</span>
            <select className="input" onChange={(event) => setPriority(event.target.value)} value={priority}>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="CRITICAL">Critical</option>
            </select>
          </div>
          <div className="field">
            <span className="field__label">Status</span>
            <select
              className="input"
              disabled={supportCase.status === "RESOLVED"}
              onChange={(event) => setStatus(event.target.value as Exclude<SupportCaseStatus, "RESOLVED">)}
              value={status}
            >
              <option value="OPEN">Open</option>
              <option value="ASSIGNED">Assigned</option>
              <option value="INVESTIGATING">Investigating</option>
              <option value="WAITING_ON_RIDER">Waiting on rider</option>
              <option value="WAITING_ON_DRIVER">Waiting on driver</option>
            </select>
          </div>
          <div className="field">
            <span className="field__label">Resolution and internal notes</span>
            <textarea
              className="input input--textarea"
              onChange={(event) => setResolutionNotes(event.target.value)}
              rows={6}
              value={resolutionNotes}
            />
          </div>
          <div className="panel__actions">
            <Button isLoading={updateMutation.isPending} onClick={handleSave} type="button" variant="secondary">
              Save case updates
            </Button>
            <Button
              disabled={supportCase.status === "RESOLVED"}
              isLoading={resolveMutation.isPending}
              onClick={handleResolve}
              type="button"
            >
              Resolve case
            </Button>
          </div>
          {error ? <ErrorDisplay message={error} title="Unable to update case" /> : null}
        </article>
      </div>
    </section>
  );
}
