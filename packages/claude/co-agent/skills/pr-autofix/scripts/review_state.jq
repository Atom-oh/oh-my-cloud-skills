# Shared validation for the host-owned checkpoint and clean transition.
def uint($max):
  type == "number" and . == floor and . >= 0 and . <= $max;
def sha($length):
  type == "string" and test("^[0-9a-f]{" + ($length | tostring) + "}$");
def valid_observation:
  . as $r | type == "object"
  and (.head | sha(40)) and (.base_sha | sha(40)) and (.diff_sha256 | sha(64))
  and (.handles | type == "array")
  and (.requirements | type == "object" and length > 0)
  and (.requirements | all(.[]; type == "object"
       and (.required | type == "boolean") and (.basis | type == "string" and test("\\S"))))
  and (.sources | type == "object" and length > 0)
  and ((.requirements | keys) == (.sources | keys))
  and (.sources | all(.[]; type == "object"
       and (.verdict | type == "string")
       and (.verdict as $v | ["PASSED","BLOCKED","ERROR","PENDING","UNBOUND","NOT_REQUIRED"] | index($v) != null)
       and (.coverage_complete | type == "boolean")
       and (.blocking_findings | type == "array")
       and (if .verdict == "UNBOUND" or .verdict == "NOT_REQUIRED"
            then .head == null or (.head | sha(40))
            else .head == $r.head end)))
  and (.sources | to_entries | all(.[]; .value.verdict != "NOT_REQUIRED"
       or $r.requirements[.key].required == false));
def valid_state:
  type == "object"
  and (.pr | uint(9007199254740991) and . > 0)
  and (.base_ref | type == "string" and length > 0)
  and (.iteration | uint(2147483647))
  and (.max_iter | uint(2147483647) and . > 0)
  and (.phase | type == "string")
  and (.phase as $p | ["poll","gate","committing","stop","awaiting_review","checking_review","finalizing"] | index($p) != null)
  and (.review == null or (.review | valid_observation))
  and (.await_limit_seconds == null or (.await_limit_seconds | uint(2147483647) and . > 0))
  and (.await_started_at == null or (.await_started_at | uint(9007199254740991)))
  and (.await_deadline == null or (.await_deadline | uint(9007199254740991)));
def ready_review:
  . as $r | valid_observation
  and (.sources | all(.[]; .verdict != "BLOCKED" and (.blocking_findings | length == 0)))
  and (.requirements | to_entries | all(.[];
       (.value.required | not)
       or ($r.sources[.key] | .verdict == "PASSED" and .coverage_complete and .head == $r.head)));
