import { useState } from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Screen, Card, Pill, Button } from '../components';
import { colors } from '../theme';
import { useExpenses } from '../expenseContext';
import { awaitingApproval, byCategory, money, totalOf, totalOfAll } from '../model';

export default function ReportsScreen() {
  const { reports, submit } = useExpenses();
  const [open, setOpen] = useState<string | null>('rep1');
  const [message, setMessage] = useState('');

  return (
    <Screen title="Expense reports" subtitle="Draft, submit and track reimbursements.">
      {message ? <Text style={styles.meta}>{message}</Text> : null}
      <View style={styles.summary}>
        <View><Text style={styles.summaryValue}>{reports.length}</Text><Text style={styles.summaryLabel}>reports</Text></View>
        <View><Text style={styles.summaryValue}>{money(totalOfAll(reports))}</Text><Text style={styles.summaryLabel}>total</Text></View>
        <View><Text style={styles.summaryValue}>{awaitingApproval(reports).length}</Text><Text style={styles.summaryLabel}>awaiting approval</Text></View>
      </View>

      {reports.map((report) => {
        const expanded = open === report.id;
        return (
          <Card key={report.id}>
            <Pressable onPress={() => setOpen(expanded ? null : report.id)}>
              <View style={styles.rowBetween}>
                <Text style={styles.title}>{report.title}</Text>
                <Pill label={report.status} tone={report.status === 'approved' ? 'ok' : report.status === 'submitted' ? 'warn' : 'default'} />
              </View>
              <View style={styles.rowBetween}>
                <Text style={styles.meta}>{report.expenses.length} expenses · {report.currency}</Text>
                <Text style={styles.amount}>{money(totalOf(report))}</Text>
              </View>
              <Text style={styles.tap}>{expanded ? 'Hide details ▲' : 'Show details ▼'}</Text>
              {expanded
                ? byCategory(report).map((group) => (
                    <Text key={group.category} style={styles.meta}>
                      {group.category}: {money(group.total)} ({group.count})
                    </Text>
                  ))
                : null}
            </Pressable>
            {expanded ? (
              <View style={styles.details}>
                {report.expenses.map((expense) => (
                  <View key={expense.id} style={styles.expenseRow}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.expenseTitle}>{expense.title}</Text>
                      <Text style={styles.meta}>{expense.date} · {expense.category}</Text>
                    </View>
                    <Text style={styles.expenseAmount}>{money(expense.amount)}</Text>
                  </View>
                ))}
                {report.status === 'draft' ? (
                  <Button
                    label="Submit report"
                    onPress={() => {
                      const answer = submit(report.id);
                      setMessage(answer.ok ? 'The report was submitted.' : answer.error ?? 'The report could not be submitted.');
                    }}
                  />
                ) : null}
              </View>
            ) : null}
          </Card>
        );
      })}
    </Screen>
  );
}

const styles = StyleSheet.create({
  summary: { flexDirection: 'row', justifyContent: 'space-between', backgroundColor: colors.brand, borderRadius: 14, padding: 14 },
  summaryValue: { color: '#fff', fontSize: 18, fontWeight: '800' },
  summaryLabel: { color: '#dbeafe', fontSize: 10 },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { fontSize: 15, fontWeight: '700', color: colors.ink, flex: 1, marginRight: 8 },
  meta: { color: colors.muted, fontSize: 11 },
  amount: { fontWeight: '800', color: colors.ink, fontSize: 15 },
  tap: { color: colors.brand, fontSize: 11, fontWeight: '600', marginTop: 2 },
  details: { borderTopWidth: 1, borderTopColor: colors.line, paddingTop: 8, gap: 6 },
  expenseRow: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 5 },
  expenseTitle: { color: colors.ink, fontSize: 13 },
  expenseAmount: { color: colors.ink, fontSize: 13, fontWeight: '600' },
});
