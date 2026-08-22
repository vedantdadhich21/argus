package com.sentinel.shield.api

import org.json.JSONArray
import org.json.JSONObject

data class HashLookupRequest(
    val sha256: String,
    val md5: String? = null
) {
    fun toJson(): String {
        val obj = JSONObject()
        obj.put("sha256", sha256)
        if (md5 != null) obj.put("md5", md5)
        return obj.toString()
    }
}

data class HashLookupResponse(
    val known: Boolean,
    val scanId: String? = null,
    val severity: String? = null,
    val finalScore: Int? = null,
    val fraudCategory: String? = null
) {
    companion object {
        fun fromJson(jsonStr: String): HashLookupResponse {
            val obj = JSONObject(jsonStr)
            val known = obj.optBoolean("known", false)
            return HashLookupResponse(
                known = known,
                scanId = if (obj.has("scan_id") && !obj.isNull("scan_id")) obj.getString("scan_id") else null,
                severity = if (obj.has("severity") && !obj.isNull("severity")) obj.getString("severity") else null,
                finalScore = if (obj.has("final_score") && !obj.isNull("final_score")) obj.getInt("final_score") else null,
                fraudCategory = if (obj.has("fraud_category") && !obj.isNull("fraud_category")) obj.getString("fraud_category") else null
            )
        }
    }
}

data class TriggerItem(
    val ruleId: String,
    val description: String,
    val weight: Int
) {
    companion object {
        fun fromJsonObject(obj: JSONObject): TriggerItem {
            val id = obj.optString("rule_id", obj.optString("id", "RULE_TRIGGER"))
            val desc = obj.optString("description", obj.optString("evidence", "Hostile signature match"))
            val weight = obj.optInt("weight", obj.optInt("points", 10))
            return TriggerItem(id, desc, weight)
        }
    }
}

data class ScanDetailResponse(
    val scanId: String,
    val status: String,
    val progressHint: String? = null,
    val severity: String? = null,
    val finalScore: Int? = null,
    val fraudCategory: String? = null,
    val triggers: List<TriggerItem> = emptyList(),
    val behaviorSummary: String? = null,
    val recommendations: List<String> = emptyList(),
    val errorMessage: String? = null
) {
    companion object {
        fun fromJson(jsonStr: String): ScanDetailResponse {
            val obj = JSONObject(jsonStr)
            val scanId = obj.optString("scan_id", "")
            val status = obj.optString("status", "queued")
            val progressHint = if (obj.has("progress_hint") && !obj.isNull("progress_hint")) obj.getString("progress_hint") else null
            val severity = if (obj.has("severity") && !obj.isNull("severity")) obj.getString("severity") else null
            val finalScore = if (obj.has("final_score") && !obj.isNull("final_score")) obj.getInt("final_score") else null
            val fraudCategory = if (obj.has("fraud_category") && !obj.isNull("fraud_category")) obj.getString("fraud_category") else null
            val behaviorSummary = if (obj.has("behavior_summary") && !obj.isNull("behavior_summary")) obj.getString("behavior_summary") else null
            val errorMessage = if (obj.has("error_message") && !obj.isNull("error_message")) obj.getString("error_message") else null

            val triggerList = mutableListOf<TriggerItem>()
            if (obj.has("triggers") && !obj.isNull("triggers")) {
                val arr = obj.getJSONArray("triggers")
                for (i in 0 until arr.length()) {
                    triggerList.add(TriggerItem.fromJsonObject(arr.getJSONObject(i)))
                }
            }

            val recList = mutableListOf<String>()
            if (obj.has("recommendations") && !obj.isNull("recommendations")) {
                val arr = obj.getJSONArray("recommendations")
                for (i in 0 until arr.length()) {
                    recList.add(arr.getString(i))
                }
            }

            return ScanDetailResponse(
                scanId = scanId,
                status = status,
                progressHint = progressHint,
                severity = severity,
                finalScore = finalScore,
                fraudCategory = fraudCategory,
                triggers = triggerList,
                behaviorSummary = behaviorSummary,
                recommendations = recList,
                errorMessage = errorMessage
            )
        }
    }
}

data class ScanHistoryItem(
    val scanId: String,
    val fileName: String,
    val score: Int,
    val severity: String,
    val category: String,
    val timestamp: Long = System.currentTimeMillis()
)
